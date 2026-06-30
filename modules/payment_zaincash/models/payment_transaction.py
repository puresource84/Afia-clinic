"""
ZainCash — transaction lifecycle methods.

Odoo 18 payment flow for redirect providers:
  _get_specific_rendering_values()  → build redirect URL shown to customer
  _get_tx_from_notification_data()  → find our TX from callback POST data
  _process_notification_data()      → update TX state from callback
"""
import logging
import pprint

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransactionZainCash(models.Model):
    _inherit = 'payment.transaction'

    # ── Step 1: Odoo builds the redirect to ZainCash ─────────────────────────

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'zaincash':
            return res

        base_url   = self.provider_id.get_base_url()
        callback   = f"{base_url}/payment/zaincash/webhook"

        token, zc_txn_id = self.provider_id._zaincash_request_token(
            amount=self.amount,
            order_id=self.reference,
            redirect_url=callback,
        )

        # Store ZainCash's transaction ID so we can match the callback
        self.provider_reference = zc_txn_id

        redirect_url = self.provider_id._zaincash_get_redirect_url(token)
        return {'redirect_url': redirect_url}

    # ── Step 2: Match callback to our transaction ─────────────────────────────

    @classmethod
    def _get_tx_from_notification_data(cls, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(
            provider_code, notification_data)
        if provider_code != 'zaincash' or len(tx) == 1:
            return tx

        # ZainCash sends 'id' (their transactionId) and 'orderId' (our reference)
        order_id = notification_data.get('orderId') or notification_data.get('order_id')
        if not order_id:
            raise ValidationError(
                "ZainCash callback missing orderId. Data: %s"
                % pprint.pformat(notification_data))

        tx = cls.search([
            ('reference', '=', order_id),
            ('provider_code', '=', 'zaincash'),
        ])
        if not tx:
            raise ValidationError(
                _("ZainCash: no transaction found for order %s") % order_id)
        return tx

    # ── Step 3: Update state from ZainCash callback ───────────────────────────

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'zaincash':
            return

        _logger.info(
            "ZainCash callback for TX %s: %s",
            self.reference, pprint.pformat(notification_data))

        status = (
            notification_data.get('status') or
            notification_data.get('msg') or ''
        ).lower()

        if status in ('success', 'paid', 'completed'):
            self._set_done()
        elif status in ('failed', 'fail', 'error', 'rejected'):
            self._set_error(
                _("ZainCash payment failed: %s") % notification_data.get('msg', status))
        elif status in ('pending', 'initiated'):
            self._set_pending()
        else:
            _logger.warning(
                "ZainCash unknown status '%s' for TX %s", status, self.reference)
            self._set_pending()
