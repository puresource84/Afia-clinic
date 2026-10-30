{
    'name': 'Dental Patient Flow Board',
    'version': '18.0.1.3.0',
    'category': 'Healthcare',
    'summary': 'Front-desk Kanban board tracking each patient from arrival to payment — all in one screen.',
    'description': "Dental Patient Flow Board\n=========================\nA real-time reception dashboard showing every patient's journey through the clinic today.\n\nKanban Columns\n--------------\n1. Expected — patients with confirmed appointments\n2. Arrived — checked in at reception\n3. Waiting — in the waiting area\n4. In Chair — currently with the dentist\n5. Done — treatment completed\n6. Payment — waiting to pay\n\nFeatures\n--------\n- Auto-populates from today's confirmed appointments\n- Drag cards between columns to update patient status\n- Card shows: patient name, dentist, appointment time, treatment type\n- Pay / Invoice button on Done and Payment columns\n- Cancellation wizard with reason capture\n- Average wait time indicator per column\n- Colour coding by appointment delay\n",
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
        'clinic_core',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cancel_wizard_views.xml',
        'views/patient_flow_board.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 0,
    'currency': 'USD',
}