{
    'name': 'Dental Sterilization Log',
    'version': '18.0.1.0.2',
    'category': 'Dental',
    'summary': 'Instrument sterilization cycle log with batch tracking, expiry dates and compliance reporting.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/sterilization_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Sterilization Log\n========================\nTrack every sterilization cycle to meet clinical hygiene compliance requirements.\n\nFeatures\n--------\n- Instrument batch creation — group instruments by type and tray\n- Sterilization cycle log: autoclave ID, cycle number, temperature, pressure, duration\n- Biological indicator test results (pass / fail) per cycle\n- Instrument package expiry date tracking\n- Alerts for instruments approaching or past expiry\n- Sterilization status visible on appointment form (all instruments ready / not ready)\n- Monthly compliance report for infection control audits\n- Supports multiple autoclave units\n\nDesigned to meet MOH and JCI dental infection control standards.\n',
    'price': 0,
    'currency': 'USD',
}
