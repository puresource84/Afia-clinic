# -*- coding: utf-8 -*-
{'name': 'Dental Patient Portal',
 'version': '18.0.1.3.0',
 'category': 'Portal',
 'summary': 'Patient self-service portal — view appointments, download invoices, prescriptions and '
            'consent documents.',
 'author': 'ITCS (IT Corner Solutions)',
 'website': 'https://www.itcornersolutions.net/',
 'license': 'OPL-1',
 'images': ['static/description/icon.png'],
 'depends': ['afia_dental_core', 'portal', 'dental_treatment_plan', 'dental_consent', 'website'],
 'data': ['views/portal_templates.xml',
          'views/portal_v2_templates.xml',
          'security/ir.model.access.csv',
          'views/templates.xml',
          'views/menus.xml',
          'views/dental_booking_slots_templates.xml',
          'views/appointment_views.xml'],
 'installable': True,
 'application': False,
 'description': 'Dental Patient Portal\n'
                '=====================\n'
                'Give patients 24/7 online access to their clinic records through the Odoo '
                'portal.\n'
                '\n'
                'Patient Can View\n'
                '----------------\n'
                '- Upcoming and past appointments\n'
                '- Treatment history and clinical summaries\n'
                '- Invoices and payment receipts (downloadable PDF)\n'
                '- Active prescriptions\n'
                '- Signed consent forms\n'
                '- Lab results (where shared by the clinic)\n'
                '\n'
                'Patient Can Do\n'
                '--------------\n'
                '- Request an appointment (routed to reception for confirmation)\n'
                '- Send a message to the clinic\n'
                '- Update contact details\n'
                '\n'
                'Portal Access\n'
                '-------------\n'
                'Patients receive a portal invitation email. Login via the standard Odoo portal.\n'
                'Multi-language: English and Arabic supported.\n'}
