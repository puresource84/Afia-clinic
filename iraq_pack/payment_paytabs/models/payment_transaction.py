"""
PayTabs — transaction lifecycle methods.

Odoo 18 payment flow for redirect providers:
  _get_specific_rendering_values()  → build redirect URL shown to customer
  _get_tx_from_notification_data()  → find our TX from callback POST data
  _process_notification_data()      → update TX state from callback
"""
import logging
import pprint

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# PayTabs response_status codes that mean "approved"
_APPROVED_STATUSES = {'A'}
# PayTabs response_status codes that mean "declined / failed"
_FAILED_STATUSES   = {'D', 'E', 'X', 'H', 'R'}
# Everything else is treated as pending (e.g. '3DS', 'H' hold, etc.)


class PaymentTransactionPayTabs(models.Model):
    _inherit = 'payment.transaction'

    # ── Step 1: Odoo builds the redirect to PayTabs ──────────────────────────

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'paytabs':
            return res

        base_url    = self.provider_id.get_base_url()
        return_url  = f"{base_url}/payment/paytabs/return"
        callback_url= f"{base_url}/payment/paytabs/webhook"

        payment_url, tran_ref = self.provider_id._paytabs_create_payment_page(
            tx=self,
            return_url=return_url,
            callback_url=callback_url,
        )

        # Store PayTabs transaction reference for callback matching
        self.provider_reference = tran_ref

        return {'redirect_url': payment_url}

    # ── Step 2: Match callback to our transaction ────────────────────────────

    @classmethod
    def _get_tx_from_notification_data(cls, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(
            provider_code, notification_data)
        if provider_code != 'paytabs' or len(tx) == 1:
            return tx

        # PayTabs sends cart_id (our reference) and tran_ref in callback
        cart_id = notification_data.get('cart_id')
        if not cart_id:
            raise ValidationError(
                "PayTabs callback missing cart_id. Data: %s"
                % pprint.pformat(notification_data))

        tx = cls.search([
            ('reference', '=', cart_id),
            ('provider_code', '=', 'paytabs'),
        ])
        if not tx:
            raise ValidationError(
                _("PayTabs: no transaction found for reference %s") % cart_id)
        return tx

    # ── Step 3: Update state from PayTabs callback ───────────────────────────

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'paytabs':
            return

        _logger.info(
            "PayTabs callback for TX %s:\n%s",
            self.reference, pprint.pformat(notification_data))

        # 2026-09-20 (afia_dental_core-paytabs-verification-bypass, found
        # in the system audit): this used to fall back to the raw,
        # UNVERIFIED webhook POST data whenever _paytabs_verify_transaction
        # raised for any reason — meaning a forced/transient verification
        # failure let an attacker-controlled payload decide payment state.
        # Server-side verification is mandatory now: if it fails, the
        # transaction is left/set pending (never marked done or failed
        # from unverified data) and the failure is logged loudly.
        # PayTabs retries webhooks on non-2xx / repeated delivery, and the
        # /payment/paytabs/return handler also calls
        # _handle_notification_data as a second chance — so a transient
        # verification failure gets another opportunity rather than being
        # silently trusted or permanently stuck.
        tran_ref = (
            notification_data.get('tran_ref') or
            self.provider_reference
        )
        if not tran_ref or not self.provider_id:
            _logger.error(
                "PayTabs: cannot verify TX %s — missing tran_ref or "
                "provider. Leaving transaction pending; raw callback data "
                "will NOT be trusted.", self.reference)
            self._set_pending()
            return

        try:
            notification_data = self.provider_id._paytabs_verify_transaction(tran_ref)
        except Exception:
            _logger.exception(
                "PayTabs: server-side verification failed for TX %s. "
                "Leaving transaction pending — raw callback data is never "
                "trusted for the done/failed decision. Will be "
                "re-evaluated on the next webhook/return delivery.",
                self.reference)
            self._set_pending()
            return

        response     = notification_data.get('payment_result', {}) or \
                       notification_data.get('response', {})
        raw_status   = (response.get('response_status') or '').upper()
        raw_message  = response.get('response_message', raw_status)

        if raw_status in _APPROVED_STATUSES:
            self._set_done()
        elif raw_status in _FAILED_STATUSES:
            self._set_error(
                _("PayTabs payment declined: %s") % raw_message)
        else:
            _logger.info(
                "PayTabs TX %s in intermediate status '%s'",
                self.reference, raw_status)
            self._set_pending()
