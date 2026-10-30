# -*- coding: utf-8 -*-
{'name': 'Dental Treatment Plans',
 'version': '18.0.1.1.0',
 'category': 'Dental',
 'summary': 'Multi-session dental treatment plans with phased scheduling, progress tracking and '
            'cost estimation.',
 'author': 'ITCS (IT Corner Solutions)',
 'website': 'https://www.itcornersolutions.net/',
 'license': 'OPL-1',
 'images': ['static/description/icon.png'],
 'depends': ['afia_dental_core', 'dental_consent', 'dental_analytics'],
 'data': ['security/ir.model.access.csv',
          'data/sequence.xml',
          'views/treatment_plan_views.xml',
          'views/menus.xml',
          'views/treatment_plan_acceptance_views.xml',
          'views/consent_signature_views.xml',
          'report/treatment_plan_proposal_report.xml'],
 'installable': True,
 'application': False,
 'description': 'Dental Treatment Plans\n'
                '======================\n'
                'Plan, schedule and track multi-visit dental treatments from diagnosis to '
                'completion.\n'
                '\n'
                'Features\n'
                '--------\n'
                '- Treatment plan header with patient, dentist, start date and total estimated '
                'cost\n'
                '- Line items: procedure, tooth reference, fee, status, assigned session\n'
                '- Phase grouping — organise lines into Phase 1 (urgent), Phase 2 (restorative), '
                'Phase 3 (elective)\n'
                '- Link each line to a specific appointment when scheduled\n'
                '- Progress bar — completed vs total procedures\n'
                '- Cost estimate vs actual cost tracking\n'
                '- Patient approval workflow (with or without e-signature)\n'
                '- Print-ready treatment plan PDF for patient\n'
                '\n'
                'Integrates with Dental Case Acceptance, Dental Lab Work Orders and Dental '
                'Insurance.\n',
 'price': 0,
 'currency': 'USD'}
