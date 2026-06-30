"""
ZainCash Payment Provider — provider-level configuration and API helpers.

ZainCash flow:
  1. POST /api/token  → receive JWT token + transactionId
  2. Redirect customer to  {base_url}/api/transaction?token={jwt}
  3. ZainCash POSTs back to our /payment/zaincash/webhook  with status

Docs: https://zaincash.iq/page/docs  (requires merchant login)
"""
import hashlib
import hmac
import json
import logging
import time

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known API endpoints
# ---------------------------------------------------------------------------
ZAINCASH_SANDBOX_URL = 'https://test.zaincash.iq'
ZAINCASH_PROD_URL    = 'https://api.zaincash.iq'

TOKEN_PATH      = '/transaction/init'
REDIRECT_PATH   = '/transaction/pay'


class PaymentProviderZainCash(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('zaincash', 'ZainCash')],
        ondelete={'zaincash': 'set default'},
    )

    # ── Credential fields ────────────────────────────────────────────────────
    zaincash_merchant_id = fields.Char(
        string='Merchant ID',
        help='Merchant ID issued by ZainCash after account approval.',
        required_if_provider='zaincash',
        groups='base.group_system',
    )
    zaincash_msisdn = fields.Char(
        string='Merchant MSISDN',
        help='Phone number registered with ZainCash as merchant wallet (e.g. 9647XXXXXXXX).',
        required_if_provider='zaincash',
        groups='base.group_system',
    )
    zaincash_secret = fields.Char(
        string='Secret Key',
        help='Secret key from ZainCash merchant portal.',
        required_if_provider='zaincash',
        groups='base.group_system',
    )
    zaincash_api_url = fields.Char(
        string='API Base URL',
        default=ZAINCASH_SANDBOX_URL,
        help='Use sandbox URL for testing, production URL for live.',
        required_if_provider='zaincash',
        groups='base.group_system',
    )

    # ── Supported features ───────────────────────────────────────────────────

    def _get_supported_currencies(self):
        supported = super()._get_supported_currencies()
        if self.code == 'zaincash':
            supported = supported.filtered(lambda c: c.name == 'IQD')
        return supported

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        providers = super()._get_compatible_providers(
            *args, currency_id=currency_id, **kwargs)
        currency = self.env['res.currency'].browse(currency_id)
        if currency and currency.name != 'IQD':
            providers = providers.filtered(lambda p: p.code != 'zaincash')
        return providers

    # ── Redirect URL helpers ─────────────────────────────────────────────────

    def _zaincash_get_api_url(self, path):
        base = (self.zaincash_api_url or ZAINCASH_SANDBOX_URL).rstrip('/')
        return base + path

    def _zaincash_get_redirect_url(self, token):
        base = (self.zaincash_api_url or ZAINCASH_SANDBOX_URL).rstrip('/')
        return f"{base}{REDIRECT_PATH}?token={token}"

    # ── Token request (Step 1) ───────────────────────────────────────────────

    def _zaincash_request_token(self, amount, order_id, redirect_url):
        """Call ZainCash /transaction/init and return (token, transactionId).

        Args:
            amount      – amount in IQD (integer)
            order_id    – unique reference string for this transaction
            redirect_url – Odoo callback URL ZainCash will POST to after payment

        Returns:
            (token: str, transaction_id: str)

        Raises:
            ValidationError on network error or ZainCash-side failure.
        """
        self.ensure_one()

        payload = {
            'merchantId':   self.zaincash_merchant_id,
            'msisdn':       self.zaincash_msisdn,
            'amount':       int(amount),
            'serviceType':  'Afia Clinic Subscription',
            'orderId':      str(order_id),
            'redirectUrl':  redirect_url,
            'iat':          int(time.time()),
            'exp':          int(time.time()) + 3600,
        }

        # ZainCash expects the payload signed as JWT using HS256
        token = self._zaincash_build_jwt(payload)

        try:
            resp = requests.post(
                self._zaincash_get_api_url(TOKEN_PATH),
                json={'token': token, 'merchantId': self.zaincash_merchant_id,
                      'lang': 'ar'},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as exc:
            _logger.exception("ZainCash token request failed: %s", exc)
            raise ValidationError(
                _("Could not connect to ZainCash. Please try again later."))

        if data.get('status') != 'success':
            msg = data.get('msg', 'Unknown error')
            _logger.error("ZainCash token error: %s | payload: %s", msg, data)
            raise ValidationError(
                _("ZainCash rejected the payment request: %s") % msg)

        return data['token'], data.get('id', '')

    # ── Minimal HS256 JWT builder (no PyJWT dependency) ─────────────────────

    def _zaincash_build_jwt(self, payload):
        """Build a minimal HS256 JWT.  Avoids external PyJWT dependency."""
        import base64

        def b64url(data):
            if isinstance(data, str):
                data = data.encode()
            return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

        header  = b64url(json.dumps({'alg': 'HS256', 'typ': 'JWT'}))
        body    = b64url(json.dumps(payload))
        signing = f"{header}.{body}".encode()
        sig     = hmac.new(
            self.zaincash_secret.encode(), signing, hashlib.sha256).digest()
        return f"{header}.{body}.{b64url(sig)}"

    # ── Webhook signature verification ───────────────────────────────────────

    def _zaincash_verify_callback(self, post_data):
        """Return True if the callback POST data is genuinely from ZainCash.

        ZainCash signs callbacks with the merchant secret.  Implement the
        exact verification method documented in your merchant agreement.
        This is a placeholder — fill in once you receive the spec from ZainCash.
        """
        # TODO: implement per ZainCash merchant documentation
        _logger.warning(
            "ZainCash callback signature verification not yet implemented. "
            "Accepting callback — MUST be secured before going live.")
        return True
