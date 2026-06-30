{
    'name': 'Dental Portal v2',
    'version': '18.0.1.0.0',
    'category': 'Healthcare/Dental',
    'summary': 'Enhanced patient portal with treatment plan approval, invoice history and consent form document download.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_patient_portal',
        'dental_case_acceptance',
        'dental_consent',
    ],
    'data': [
        'views/portal_v2_templates.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Portal v2\n================\nExtends the base Dental Patient Portal with interactive treatment plan management.\n\nAdded Features\n--------------\n- Treatment plan review page — patient can view proposed treatments with costs\n- Online acceptance / rejection of individual treatment plan lines\n- E-signature on treatment plan acceptance (touch-compatible)\n- Complete dental invoice history with PDF download\n- Consent form document library (download signed copies)\n- Secure document share link (shareable without portal login, time-limited)\n- Portal notification badge for new documents\n\nRequires: dental_patient_portal\n',
    'price': 0,
    'currency': 'USD',
}
