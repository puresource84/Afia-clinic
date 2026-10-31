# -*- coding: utf-8 -*-
{'name': 'Afia Clinic',
 'version': '18.0.1.0.0',
 'category': 'Healthcare',
 'summary': 'Complete dental clinic suite: patients, appointments, charting, billing, insurance, '
            'lab and portal. Installs everything in one click.',
 'description': 'Afia Clinic\n'
                '===========\n'
                '\n'
                'Install this one module to get the whole suite. It pulls in every Afia\n'
                'Clinic module through its dependencies, so nothing has to be installed by\n'
                'hand.\n'
                '\n'
                'Included\n'
                '--------\n'
                '- Patients, appointments and the daily patient-flow board\n'
                '- FDI odontogram, periodontal charting and visit imaging\n'
                '- Treatment plans, consent forms and clinical (SOAP) notes\n'
                '- Prescriptions with allergy checking\n'
                '- Billing, insurance claims and the lab workflow\n'
                '- Consumables and sterilisation tracking\n'
                '- Patient portal and online booking\n'
                '- WhatsApp and Telegram reminders\n'
                '- Role-based access for Administrator, Dentist, Hygienist and Receptionist\n'
                '- Arabic interface throughout\n',
 'author': 'ITCS (IT Corner Solutions)',
 'website': 'https://www.itcornersolutions.net/',
 'support': 'support@itcornersolutions.net',
 'license': 'OPL-1',
 'depends': ['afia_app_launcher',
             'afia_dental_core',
             'afia_menu',
             'dental_allergy_guard',
             'dental_analytics',
             'dental_audit',
             'dental_charting',
             'dental_clinical_permissions',
             'dental_consent',
             'dental_consumables',
             'dental_demo_data',
             'dental_insurance',
             'dental_lab',
             'dental_patient_flow',
             'dental_portal',
             'dental_reminders',
             'dental_soap_notes',
             'dental_sterilization',
             'dental_treatment_plan'],
 'data': [],
 # First entry is the artwork the Odoo App Store shows on the listing page.
 # icon.png stays listed so the tile and the listing stay in step.
 'images': ['static/description/banner.png',
            'static/description/icon.png'],
 'installable': True,
 'application': True,
 'auto_install': False,
 'price': 299,
 'currency': 'USD'}
