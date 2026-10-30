# -*- coding: utf-8 -*-
{'name': 'Dental Audit Trail',
 'version': '18.0.1.2.1',
 'category': 'Healthcare/Dental',
 'summary': 'Field-level audit trail on all clinical records — every change is logged with user, '
            'timestamp and old value.',
 'author': 'ITCS (IT Corner Solutions)',
 'website': 'https://www.itcornersolutions.net/',
 'license': 'OPL-1',
 'depends': ['afia_dental_core',
             'dental_treatment_plan',
             'dental_consent',
             'dental_charting',
             'dental_allergy_guard'],
 'data': ['views/audit_views.xml'],
 'images': ['static/description/icon.png'],
 'installable': True,
 'application': False,
 'description': 'Dental Clinical Audit Trail\n'
                '===========================\n'
                'Adds comprehensive change tracking to all key clinical models.\n'
                '\n'
                'Tracked Models\n'
                '--------------\n'
                '- Patient records (demographics, allergies, medical history)\n'
                '- Appointments (status changes, reschedules)\n'
                '- Clinical notes and SOAP entries\n'
                '- Treatment plans and plan lines\n'
                '- Prescriptions\n'
                '- Consent forms\n'
                '\n'
                'Audit Log Features\n'
                '------------------\n'
                '- Field-level diff: shows old value → new value\n'
                '- User, date-time and IP address recorded per change\n'
                '- Filterable audit log view accessible to Clinic Manager\n'
                '- Export audit report to PDF for compliance reviews\n'
                '- Tamper-evident: audit records are read-only after creation\n'
                '\n'
                'Supports JCI, MOH and ISO 27001 audit requirements.\n',
 'price': 0,
 'currency': 'USD'}
