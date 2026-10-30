"""
ZainCash payment webhook controller.

ZainCash POSTs back to /payment/zaincash/webhook after the customer
completes (or cancels) payment on the ZainCash hosted page.

Expected POST fields (from ZainCash docs):
    id            – ZainCash transaction ID
    orderId       – our reference (what we sent as orderId in the JWT)
    status        – 'success' | 'failed' | 'pending'
    msg           – human-readable status message
    amount        – amount paid in IQD
    type          – transaction type
"""
import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ZainCashController(http.Controller):

    _webhook_url = '/payment/zaincash/webhook'

    @http.route(
        _webhook_url,
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,          # ZainCash cannot send CSRF token
        save_session=False,
    )
    def zaincash_webhook(self, **post):
        """Handle the POST callback from ZainCash."""
        _logger.info(
            "ZainCash webhook received:\n%s", pprint.pformat(post))

        try:
            # Find the provider to run signature verification
            provider = request.env['payment.provider'].sudo().search(
                [('code', '=', 'zaincash'), ('state', '!=', 'disabled')],
                limit=1,
            )
            if not provider:
                _logger.warning("ZainCash webhook: no active provider found.")
                return request.make_response('OK')

            if not provider._zaincash_verify_callback(post):
                _logger.error(
                    "ZainCash webhook: signature verification failed. "
                    "Data: %s", pprint.pformat(post))
                return request.make_response('INVALID SIGNATURE', status=400)

            # Let the payment framework route to the right transaction
            request.env['payment.transaction'].sudo()._handle_notification_data(
                'zaincash', post)

        except Exception:
            _logger.exception(
                "ZainCash webhook: unhandled exception for data: %s",
                pprint.pformat(post))
            # Always return 200 to prevent ZainCash from retrying endlessly
            return request.make_response('OK')

        return request.make_response('OK')
