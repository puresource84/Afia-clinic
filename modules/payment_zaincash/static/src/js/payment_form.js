/** @odoo-module **/
/**
 * ZainCash – frontend payment form integration.
 *
 * ZainCash uses a server-side redirect flow:
 *   1. Customer clicks "Pay with ZainCash"
 *   2. Odoo backend calls ZainCash API, gets a redirect token
 *   3. Browser is sent to ZainCash hosted payment page
 *   4. ZainCash POSTs back to /payment/zaincash/webhook
 *
 * Because this is a pure redirect provider, we need almost no custom JS —
 * Odoo's base payment form handles the redirect.  This file exists to
 * register ZainCash with the payment form mixin so Odoo knows it is a
 * redirect (not an inline/card) provider.
 */

import { _t } from "@web/core/l10n/translation";
import { PaymentForm } from "@payment/js/payment_form";
import { patch } from "@web/core/utils/patch";

patch(PaymentForm.prototype, {

    // ── Provider type detection ──────────────────────────────────────────────

    /**
     * ZainCash is always a redirect provider.
     * The parent method checks provider_type from the server; we simply
     * ensure the redirect template is used for 'zaincash' codes.
     */
    _isRedirectProviderCode(providerCode) {
        if (providerCode === 'zaincash') return true;
        return super._isRedirectProviderCode?.(providerCode) ?? false;
    },

    // ── Payment processing ───────────────────────────────────────────────────

    async _processRedirectPayment(providerCode, paymentOptionId, processingValues) {
        if (providerCode !== 'zaincash') {
            return super._processRedirectPayment(
                providerCode, paymentOptionId, processingValues);
        }

        // redirect_url was set by _get_specific_rendering_values on the server
        const { redirect_url: redirectUrl } = processingValues;
        if (!redirectUrl) {
            this._displayError(
                _t("Payment Error"),
                _t("ZainCash did not return a payment URL. Please try again."),
            );
            return;
        }

        window.location = redirectUrl;
    },
});
