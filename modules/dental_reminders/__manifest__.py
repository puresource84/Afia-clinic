# -*- coding: utf-8 -*-
{'name': 'Dental Communication',
 'version': '18.0.1.3.0',
 'category': 'Dental',
 'summary': 'Automated appointment reminders, recall campaigns and patient communication log via '
            'email and SMS.',
 'author': 'ITCS (IT Corner Solutions)',
 'website': 'https://www.itcornersolutions.net/',
 'license': 'OPL-1',
 'images': ['static/description/icon.png'],
 'depends': ['afia_dental_core', 'mail'],
 'data': ['data/email_templates.xml',
          'data/cron_jobs.xml',
          'data/dental_reminders_whatsapp_cron_jobs.xml',
          'views/res_config_settings_views.xml',
          'data/dental_reminders_telegram_cron_jobs.xml',
          'views/dental_reminders_telegram_res_config_settings_views.xml',
          'views/res_partner_views.xml',
          'reports/telegram_card_report.xml',
          'security/ir.model.access.csv',
          'data/telegram_templates.xml',
          'views/telegram_template_views.xml'],
 'installable': True,
 'application': False,
 'description': 'Dental Communication & Reminders\n'
                '=================================\n'
                'Keep patients informed and reduce no-shows with automated multi-channel '
                'communication.\n'
                '\n'
                'Features\n'
                '--------\n'
                '- Appointment reminders: 24-hour and 2-hour before, via email and/or SMS\n'
                '- Recall campaigns — contact patients due for 6-month check-up\n'
                '- Birthday greetings (optional)\n'
                '- Communication log on patient record showing every message sent\n'
                '- Configurable message templates with patient name, date and dentist merge '
                'fields\n'
                '- Unsubscribe / opt-out tracking\n'
                '- Manual send option from the appointment form\n'
                '\n'
                'Integrates with Dental Telegram Reminders and Dental WhatsApp Reminders for '
                'additional channels.\n',
 'price': 0,
 'currency': 'USD'}
