/** @odoo-module **/
/**
 * PayTabs – frontend payment form integration.
 *
 * PayTabs uses a redirect flow identical to ZainCash:
 *   1. Customer clicks "Pay with PayTabs"
 *   2. Backend calls PayTabs API, gets a hosted payment URL
 *   3. Browser is redirected to PayTabs hosted page
 *   4. PayTabs POSTs to /payment/paytabs/webhook (server callback)
 *   5. Customer browser is sent to /payment/paytabs/return
 */

import { _t } from "@web/core/l10n/translation";
import { PaymentForm } from "@payment/js/payment_form";
import { patch } from "@web/core/utils/patch";

// Guard 2026-07-16: this asset is currently disabled in __manifest__.py (see
// the comment there for why — PaymentForm previously didn't resolve at this
// import path in this Odoo build and crashed the ENTIRE frontend bundle,
// including the login page, because the whole site shares one bundle). If
// this file is ever re-enabled without first confirming PaymentForm exists,
// this guard prevents that same site-wide crash — it logs a warning and
// skips the patch instead of throwing on `undefined.prototype`.
if (PaymentForm) {
    patch(PaymentForm.prototype, {

        _isRedirectProviderCode(providerCode) {
            if (providerCode === 'paytabs') return true;
            return super._isRedirectProviderCode?.(providerCode) ?? false;
        },

        async _processRedirectPayment(providerCode, paymentOptionId, processingValues) {
            if (providerCode !== 'paytabs') {
                return super._processRedirectPayment(
                    providerCode, paymentOptionId, processingValues);
            }

            const { redirect_url: redirectUrl } = processingValues;
            if (!redirectUrl) {
                this._displayError(
                    _t("Payment Error"),
                    _t("PayTabs did not return a payment URL. Please try again."),
                );
                return;
            }

            window.location = redirectUrl;
        },
    });
} else {
    console.warn(
        "[payment_paytabs] PaymentForm not found at @payment/js/payment_form — " +
        "skipping patch. This module's frontend API has likely changed; " +
        "payment_paytabs/static/src/js/payment_form.js needs updating."
    );
}
