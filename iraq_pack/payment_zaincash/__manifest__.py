{
    'name': 'Payment: ZainCash',
    'version': '18.0.1.0.3',
    'category': 'Accounting/Payment Providers',
    'summary': "ZainCash mobile wallet payment integration for Odoo — Iraq's leading digital payment solution.",
    'description': 'Payment Provider: ZainCash\n==========================\nIntegrates ZainCash as a payment provider in Odoo for Iraqi merchants.\n\nSupported Payment Methods\n-------------------------\n- ZainCash wallet (customer pays from ZainCash mobile app)\n- Redirect to ZainCash hosted payment page\n\nFeatures\n--------\n- Standard Odoo payment provider integration\n- IQD currency support\n- Payment confirmation via ZainCash callback\n- Transaction reference stored on the payment record\n- Test environment support\n- Works with Odoo eCommerce, Invoices and the Dental patient portal\n\nSetup\n-----\n1. Obtain your Merchant ID, Secret and API URL from ZainCash\n2. Enter credentials in Accounting → Configuration → Payment Providers → ZainCash\n3. Activate and run a test transaction before going live\n',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_zaincash_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    # DISABLED 2026-07-16: same bug class as payment_paytabs — payment_form.js
    # imports `PaymentForm` from `@payment/js/payment_form`, which doesn't
    # exist at that path in this Odoo 18 build, so `patch(PaymentForm
    # .prototype, ...)` throws undefined at module-load time and crashes the
    # entire web.assets_frontend bundle site-wide (including the login page).
    # Disabled until rewritten against the current payment module's actual
    # frontend API. Dormant/future-use gateway per Manhel's 2026-07-15
    # direction — backend models/webhook untouched, only this asset
    # registration is disabled.
    # 'assets': {'web.assets_frontend': ['payment_zaincash/static/src/js/payment_form.js']},
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 0,
    'currency': 'USD',
}
