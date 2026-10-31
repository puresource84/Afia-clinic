# -*- coding: utf-8 -*-
{'name': 'Dental Insurance & Claims',
 'version': '18.0.1.1.0',
 'category': 'Dental',
 'summary': 'Insurance policy management, pre-authorisation requests and claims submission for '
            'dental clinics.',
 'author': 'ITCS (IT Corner Solutions)',
 'website': 'https://www.itcornersolutions.net/',
 'license': 'OPL-1',
 'images': ['static/description/icon.png'],
 'depends': ['afia_dental_core', 'account'],
 'data': ['security/ir.model.access.csv',
          'data/sequence.xml',
          'views/dental_insurance_views.xml',
          'views/menus.xml',
          'views/claim_v2_views.xml',
          'report/claim_form_report.xml'],
 'installable': True,
 'application': False,
 'description': 'Dental Insurance & Claims\n'
                '=========================\n'
                'Full insurance workflow management for dental practices working with insurance '
                'providers.\n'
                '\n'
                'Features\n'
                '--------\n'
                '- Insurance company and policy catalogue\n'
                '- Patient insurance card linked to patient record\n'
                '- Coverage rules per policy (procedures covered, co-pay percentage, annual '
                'limit)\n'
                '- Pre-authorisation request creation and tracking\n'
                '- Claim generation from completed invoices\n'
                '- Claim status workflow: draft → submitted → approved / rejected\n'
                '- Co-pay calculation and patient balance invoicing\n'
                '- Insurance ageing report — outstanding claims by payer\n'
                '\n'
                'Upgrade with Dental Insurance v2 for document attachments and payer-specific '
                'print templates.\n'}
