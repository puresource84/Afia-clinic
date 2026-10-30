# -*- coding: utf-8 -*-
{'name': 'Dental Patient Flow Board',
 'version': '18.0.1.4.0',
 'category': 'Healthcare',
 'summary': 'Front-desk Kanban board tracking each patient from arrival to payment — all in one '
            'screen.',
 'description': 'Dental Patient Flow Board\n'
                '=========================\n'
                "A real-time reception dashboard showing every patient's journey through the "
                'clinic today.\n'
                '\n'
                'Kanban Columns\n'
                '--------------\n'
                '1. Expected — patients with confirmed appointments\n'
                '2. Arrived — checked in at reception\n'
                '3. Waiting — in the waiting area\n'
                '4. In Chair — currently with the dentist\n'
                '5. Done — treatment completed\n'
                '6. Payment — waiting to pay\n'
                '\n'
                'Features\n'
                '--------\n'
                "- Auto-populates from today's confirmed appointments\n"
                '- Drag cards between columns to update patient status\n'
                '- Card shows: patient name, dentist, appointment time, treatment type\n'
                '- Pay / Invoice button on Done and Payment columns\n'
                '- Cancellation wizard with reason capture\n'
                '- Average wait time indicator per column\n'
                '- Colour coding by appointment delay\n',
 'author': 'ITCS (IT Corner Solutions)',
 'website': 'https://www.itcornersolutions.net/',
 'license': 'OPL-1',
 'depends': ['afia_dental_core', 'account'],
 'data': ['security/ir.model.access.csv',
          'views/cancel_wizard_views.xml',
          'views/patient_flow_board.xml',
          'views/appointment_times_views.xml'],
 'images': ['static/description/icon.png'],
 'installable': True,
 'auto_install': False,
 'application': False,
 'price': 0,
 'currency': 'USD',
 'assets': {'web.assets_backend': ['dental_patient_flow/static/src/xml/float_time_dropdown.xml',
                                   'dental_patient_flow/static/src/js/float_time_dropdown.js']}}
