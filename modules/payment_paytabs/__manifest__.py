{
    'name': 'Payment Provider: PayTabs',
    'version': '18.0.1.0.0',
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
    'assets': {'web.assets_frontend': ['payment_paytabs/static/src/js/payment_form.js']},
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': False,
    'price': 0,
    'currency': 'USD',
}
