# -*- coding: utf-8 -*-
{'name': 'Dental Clinic Menu',
 'version': '18.0.1.0.0',
 'category': 'Dental',
 'summary': 'Reorganises the dental clinic menu into intuitive Patient and Billing groups for '
            'faster navigation.',
 'author': 'ITCS (IT Corner Solutions)',
 'website': 'https://www.itcornersolutions.net/',
 'license': 'OPL-1',
 'images': ['static/description/icon.png'],
 'depends': ['afia_dental_core',
             'dental_treatment_plan',
             'dental_lab',
             'dental_consent',
             'dental_sterilization',
             'dental_insurance',
             'dental_analytics',
             'dental_portal'],
 'data': ['views/menu_patch.xml'],
 'installable': True,
 'auto_install': False,
 'application': False,
 'description': 'Dental Clinic Menu Restructure\n'
                '==============================\n'
                'Replaces the default scattered menu with a clean two-group layout.\n'
                '\n'
                'Patient Group\n'
                '-------------\n'
                '- Patient records, appointments, charting, clinical notes, imaging\n'
                '\n'
                'Billing Group\n'
                '-------------\n'
                '- Invoices, insurance claims, payments, financial reports\n'
                '\n'
                'Benefits\n'
                '--------\n'
                '- Reception staff find billing tasks instantly without scrolling past clinical '
                'menus\n'
                '- Clinicians see only clinical items during consultations\n'
                "- Fully compatible with Odoo's standard access rights\n",
 'price': 0,
 'currency': 'USD'}
