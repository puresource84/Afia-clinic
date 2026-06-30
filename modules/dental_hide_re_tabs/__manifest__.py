{
    'name': 'Dental — Hide Alpha RE Tabs (bridge)',
    'version': '18.0.1.0.0',
    'category': 'Healthcare/Dental',
    'summary': 'Bridge module that hides Alpha Real Estate tabs on patient records when both suites are installed together.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_hospital',
        'real_estate_account',
        'real_estate_contract',
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
    'description': 'Dental — Hide Alpha RE Tabs\n===========================\nA lightweight bridge module for clinics that also use the Alpha Real Estate suite.\n\nProblem Solved\n--------------\nWhen both the Afia Clinic suite and the Alpha Real Estate suite are installed in the\nsame Odoo database, real estate-related tabs appear on patient records — confusing\nclinical staff.\n\nSolution\n--------\nThis module detects the presence of both suites and hides the irrelevant real estate\ntabs from the patient form view using view inheritance.\n\nNotes\n-----\n- Auto-installs only when both dental_hospital and the RE suite are present\n- No configuration required\n- Safe to uninstall — original tabs reappear\n',
    'price': 0,
    'currency': 'USD',
}
