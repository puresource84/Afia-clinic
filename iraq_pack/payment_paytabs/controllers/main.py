"""
PayTabs payment webhook and return controllers.

PayTabs makes two kinds of requests:
  1. Server-to-server callback POST → /payment/paytabs/webhook
     (called immediately after payment, regardless of browser state)
  2. Browser return GET/POST       → /payment/paytabs/return
     (customer lands here after PayTabs hosted page; less reliable)

We process state from the server-to-server callback (webhook) and use
the return URL only to redirect the customer to the Odoo thank-you page.
"""
import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PayTabsController(http.Controller):

    _webhook_url = '/payment/paytabs/webhook'
    _return_url  = '/payment/paytabs/return'

    # ── Server-to-server callback ────────────────────────────────────────────

    @http.route(
        _webhook_url,
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
        save_session=False,
    )
    def paytabs_webhook(self, **post):
        """Handle the server-to-server payment notification from PayTabs."""
        _logger.info("PayTabs webhook received:\n%s", pprint.pformat(post))

        try:
            request.env['payment.transaction'].sudo()._handle_notification_data(
                'paytabs', post)
        except Exception:
            _logger.exception(
                "PayTabs webhook: unhandled exception for data: %s",
                pprint.pformat(post))

        # Always return 200 — PayTabs retries on non-200
        return request.make_response('OK')

    # ── Browser return URL ───────────────────────────────────────────────────

    @http.route(
        _return_url,
        type='http',
        auth='public',
        methods=['GET', 'POST'],
        csrf=False,
        website=True,
    )
    def paytabs_return(self, **post):
        """
        Customer lands here after completing payment on PayTabs hosted page.

        PayTabs also POSTs transaction data here — process it as a fallback
        in case the webhook hasn't fired yet, then redirect to thank-you.
        """
        _logger.info("PayTabs return received:\n%s", pprint.pformat(post))

        # Process as notification data (the webhook may beat us here)
        if post.get('cart_id') or post.get('tran_ref'):
            try:
                request.env['payment.transaction'].sudo()._handle_notification_data(
                    'paytabs', post)
            except Exception:
                _logger.warning(
                    "PayTabs return: could not process notification data: %s",
                    pprint.pformat(post), exc_info=True)

        # Find the transaction so we can redirect to the correct URL
        tx_sudo = request.env['payment.transaction'].sudo().search(
            [('reference', '=', post.get('cart_id')),
             ('provider_code', '=', 'paytabs')],
            limit=1,
        )
        return request.redirect(
            '/payment/status' if not tx_sudo else
            '/payment/status?tx_id=%d' % tx_sudo.id
        )
