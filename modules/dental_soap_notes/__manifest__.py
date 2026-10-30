# -*- coding: utf-8 -*-
{'name': 'Dental SOAP Notes',
 'version': '18.0.1.4.0',
 'category': 'Healthcare/Dental',
 'summary': 'Structured S/O/A/P clinical notes with content library, procedure templates and '
            'multi-visit history.',
 'author': 'ITCS (IT Corner Solutions)',
 'website': 'https://www.itcornersolutions.net/',
 'license': 'OPL-1',
 'depends': ['afia_dental_core', 'dental_clinical_permissions'],
 'data': ['reports/soap_note_report.xml',
          'security/ir.model.access.csv',
          'security/soap_security.xml',
          'data/soap_templates.xml',
          'data/soap_sentences.xml',
          'views/soap_template_views.xml',
          'views/soap_sentence_views.xml',
          'views/soap_note_views.xml',
          'views/appointment_soap_button.xml'],
 'images': ['static/description/icon.png'],
 'installable': True,
 'application': False,
 'description': 'Dental SOAP Clinical Notes\n'
                '==========================\n'
                'Replace free-text clinical notes with structured, searchable SOAP documentation.\n'
                '\n'
                'SOAP Structure\n'
                '--------------\n'
                "- Subjective — patient's chief complaint and symptoms in their own words\n"
                '- Objective — clinical findings, vital signs, examination results\n'
                '- Assessment — diagnosis codes (ICD-10 / SNODENT), severity grading\n'
                '- Plan — proposed treatments, referrals, prescriptions, follow-up instructions\n'
                '\n'
                'Features\n'
                '--------\n'
                '- Content library — save and reuse common clinical phrases\n'
                '- Procedure templates — pre-fill the Plan section from the treatment catalogue\n'
                '- Linked to the appointment, charting and treatment plan in one screen\n'
                '- Multi-visit history tab showing all previous SOAP notes for the patient\n'
                '- Clinical note PDF for patient records and referral letters\n'
                '- Voice-to-text input support (browser-native)\n'
                '- Clinician signature and timestamp on each note\n'}
