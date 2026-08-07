{
    'name': 'Dental Consent Forms',
    'version': '18.0.1.0.2',
    'category': 'Dental',
    'summary': 'Digital consent form library with patient-specific consent tracking, status and PDF archive.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'images': ['static/description/icon.png'],
    'depends': [
        'afia_dental_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/consent_templates.xml',
        'views/consent_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Consent Forms\n====================\nManage the full lifecycle of patient consent digitally.\n\nFeatures\n--------\n- Consent form template library (general, surgical, anaesthesia, imaging, data)\n- Assign forms to a patient visit with one click\n- Track consent status: pending, signed, declined, expired\n- Link consent to treatment plans — plan cannot proceed without required consent\n- PDF generation of completed consent forms\n- Consent expiry alerts (e.g. annual review forms)\n- Consent history per patient\n\nWorks with Dental Case Acceptance for tablet-based e-signature capture.\n',
    'price': 0,
    'currency': 'USD',
}
