{
    'name': 'Payment Provider: ZainCash',
    'version': '18.0.1.0.0',
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
    'assets': {'web.assets_frontend': ['payment_zaincash/static/src/js/payment_form.js']},
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 0,
    'currency': 'USD',
}
