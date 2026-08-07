{
    'name': 'Clinic Core',
    'version': '18.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Shared foundation module for the Afia Clinic suite — models, security groups and base configuration.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'base',
        'mail',
        'afia_dental_core',
    ],
    'data': [
        'security/clinic_security.xml',
        'views/clinic_menu.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'description': 'Clinic Core\n===========\nThe required base module for the Afia Clinic suite.\n\nProvides\n--------\n- Core database models shared across all Afia Clinic modules\n- Security group definitions (Clinic Manager, Receptionist, Clinician, Lab Tech)\n- Base configuration settings page\n- Company-level clinic preferences (currency, working hours, default branch)\n\nThis module must be installed before any other Afia Clinic module.\n',
    'price': 0,
    'currency': 'USD',
}
