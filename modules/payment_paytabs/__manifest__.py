{
    'name': 'Payment Provider: PayTabs',
    'version': '18.0.1.0.1',
    'category': 'Accounting/Payment Providers',
    'summary': 'PayTabs payment gateway integration for Odoo — card payments for merchants in Iraq and the GCC.',
    'description': "Payment Provider: PayTabs\n=========================\nAdds PayTabs as a fully integrated payment provider in Odoo.\n\nSupported Payment Methods\n-------------------------\n- Visa / Mastercard (3D Secure)\n- PayTabs hosted payment page\n\nFeatures\n--------\n- Configuration in Odoo's standard Payment Providers settings\n- Automatic payment confirmation via webhook\n- Refund support from Odoo backend\n- Test mode / live mode toggle\n- IQD (Iraqi Dinar) and USD currency support\n- Transaction log with PayTabs reference number\n\nSetup\n-----\n1. Create a PayTabs account and obtain your Profile ID and Server Key\n2. Enter credentials in Accounting → Configuration → Payment Providers → PayTabs\n3. Activate and test with the PayTabs sandbox\n",
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_paytabs_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    # DISABLED 2026-07-16: payment_form.js imports `PaymentForm` from
    # `@payment/js/payment_form`, but that class does not exist at that path
    # in this Odoo 18 build (the `payment` module's frontend JS was
    # restructured), so `PaymentForm` is undefined and `patch(PaymentForm
    # .prototype, ...)` throws at module-load time. Because this asset was
    # registered under 'web.assets_frontend', the crash broke the ENTIRE
    # frontend bundle site-wide (including the login page, which renders
    # through the website/frontend layout on this instance) — not just the
    # checkout flow. Disabled here until the JS is rewritten against the
    # current payment module's actual frontend API. Dormant/future-use
    # payment gateway per Manhel's 2026-07-15 direction (same treatment as
    # payment_zaincash) — backend models/webhook are untouched, only this
    # asset registration is disabled.
    # 'assets': {'web.assets_frontend': ['payment_paytabs/static/src/js/payment_form.js']},
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': False,
    'price': 0,
    'currency': 'USD',
}
