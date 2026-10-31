"""
PayTabs Payment Provider — provider-level configuration and API helpers.

PayTabs hosted-payment flow:
  1. POST /payment/request  →  receive payment_url + tran_ref
  2. Redirect customer to   payment_url
  3. PayTabs POSTs callback to our /payment/paytabs/webhook with tran_ref + status

PayTabs API docs: https://site.paytabs.com/en/developer-tools/
Iraq region endpoint: https://secure.paytabs.sa  (MENA region server)
"""
import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PayTabs API constants
# ---------------------------------------------------------------------------
PAYTABS_MENA_URL    = 'https://secure.paytabs.sa'    # Iraq/MENA merchants
PAYTABS_SANDBOX_URL = 'https://secure-egypt.paytabs.com'  # use for test profile

REQUEST_PATH  = '/payment/request'
VERIFY_PATH   = '/payment/query'

# Supported currencies for Iraqi merchants
_IQ_CURRENCIES = {'IQD', 'USD', 'EUR'}


class PaymentProviderPayTabs(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('paytabs', 'PayTabs')],
        ondelete={'paytabs': 'set default'},
    )

    # ── Credential fields ────────────────────────────────────────────────────
    paytabs_profile_id = fields.Char(
        string='Profile ID',
        help='Your PayTabs merchant profile ID from the merchant portal.',
        required_if_provider='paytabs',
        groups='base.group_system',
    )
    paytabs_server_key = fields.Char(
        string='Server Key',
        help='Server key (secret) from PayTabs merchant portal → Developers → Key.',
        required_if_provider='paytabs',
        groups='base.group_system',
    )
    paytabs_region = fields.Selection(
        string='Region / Endpoint',
        selection=[
            ('https://secure.paytabs.sa',          'MENA (Iraq, Saudi, UAE …)'),
            ('https://secure-egypt.paytabs.com',   'Egypt'),
            ('https://secure.paytabs.com',         'Global'),
        ],
        default='https://secure.paytabs.sa',
        required_if_provider='paytabs',
        groups='base.group_system',
        help='Choose the PayTabs regional endpoint that matches your merchant account.',
    )

    # ── Supported features ───────────────────────────────────────────────────

    def _get_supported_currencies(self):
        supported = super()._get_supported_currencies()
        if self.code == 'paytabs':
            supported = supported.filtered(
                lambda c: c.name in _IQ_CURRENCIES)
        return supported

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        providers = super()._get_compatible_providers(
            *args, currency_id=currency_id, **kwargs)
        if currency_id:
            currency = self.env['res.currency'].browse(currency_id)
            if currency and currency.name not in _IQ_CURRENCIES:
                providers = providers.filtered(
                    lambda p: p.code != 'paytabs')
        return providers

    # ── API helpers ──────────────────────────────────────────────────────────

    def _paytabs_get_api_url(self, path):
        base = (self.paytabs_region or PAYTABS_MENA_URL).rstrip('/')
        return base + path

    def _paytabs_get_headers(self):
        return {
            'Authorization': self.paytabs_server_key or '',
            'Content-Type':  'application/json',
        }

    # ── Payment page request (Step 1) ────────────────────────────────────────

    def _paytabs_create_payment_page(self, tx, return_url, callback_url):
        """
        Call PayTabs /payment/request and return (payment_url, tran_ref).

        Args:
            tx           – payment.transaction record
            return_url   – where to send the customer after payment (Odoo thank-you)
            callback_url – where PayTabs POSTs the server-to-server notification

        Returns:
            (payment_url: str, tran_ref: str)

        Raises:
            ValidationError on connection or API error.
        """
        self.ensure_one()

        # Build the customer billing object from the tx partner
        partner = tx.partner_id
        payload = {
            'profile_id':  self.paytabs_profile_id,
            'tran_type':   'sale',
            'tran_class':  'ecom',
            'cart_id':     tx.reference,
            'cart_description': 'Afia Clinic — %s' % tx.reference,
            'cart_currency': tx.currency_id.name,
            'cart_amount':   tx.amount,
            'callback':    callback_url,
            'return':      return_url,
            'customer_details': {
                'name':    partner.name or 'Customer',
                'email':   partner.email or '',
                'phone':   partner.phone or partner.mobile or '',
                'street1': partner.street or '',
                'city':    partner.city or '',
                'state':   partner.state_id.name if partner.state_id else '',
                'country': partner.country_id.code if partner.country_id else 'IQ',
                'zip':     partner.zip or '',
            },
        }

        try:
            resp = requests.post(
                self._paytabs_get_api_url(REQUEST_PATH),
                json=payload,
                headers=self._paytabs_get_headers(),
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as exc:
            _logger.exception("PayTabs payment request failed: %s", exc)
            raise ValidationError(
                _("Could not connect to PayTabs. Please try again later."))

        if data.get('response', {}).get('response_status') != 'A':
            msg = (data.get('response', {}).get('response_message')
                   or data.get('trace', 'Unknown error'))
            _logger.error("PayTabs payment request error: %s | data: %s", msg, data)
            raise ValidationError(
                _("PayTabs rejected the payment request: %s") % msg)

        return data['redirect_url'], data['tran_ref']

    # ── Transaction verification ─────────────────────────────────────────────

    def _paytabs_verify_transaction(self, tran_ref):
        """
        Query PayTabs for the current status of a transaction.

        Returns the raw response dict from PayTabs.
        Raises ValidationError on network failure.
        """
        self.ensure_one()
        try:
            resp = requests.post(
                self._paytabs_get_api_url(VERIFY_PATH),
                json={'profile_id': self.paytabs_profile_id, 'tran_ref': tran_ref},
                headers=self._paytabs_get_headers(),
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as exc:
            _logger.exception("PayTabs verify call failed: %s", exc)
            raise ValidationError(
                _("Could not verify payment with PayTabs."))
