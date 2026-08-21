{
    'name': 'Dental Charting Pro',
    'version': '18.0.1.7.4',
    'category': 'Healthcare/Dental',
    'summary': 'Interactive FDI odontogram with per-tooth conditions, surface mapping and full clinical history.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
        'mail',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'report/dental_chart_report.xml',
        'views/dental_tooth_record_views.xml',
    ],
    'assets': {'web.assets_backend': ['dental_charting_pro/static/src/odontogram/odontogram.js', 'dental_charting_pro/static/src/odontogram/odontogram.xml']},
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
    'description': 'Dental Charting Pro (Odontogram)\n================================\nA full-featured interactive dental chart built on the FDI numbering system.\n\nFeatures\n--------\n- Visual FDI odontogram — click any tooth to record conditions\n- Surface mapping — buccal, lingual, mesial, distal, occlusal per tooth\n- Condition codes: caries, filling, crown, bridge, missing, implant, and more\n- History timeline — view the chart state at any past visit\n- Paediatric chart mode (primary dentition)\n- Print-ready chart report (PDF)\n- Links directly to SOAP notes and treatment plan lines\n\nCompatible with Dental SOAP Notes and Dental Perio Charting.\n',
    'price': 0,
    'currency': 'USD',
}