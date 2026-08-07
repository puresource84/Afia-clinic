{
    'name': 'Dental Communication',
    'version': '18.0.1.0.1',
    'category': 'Dental',
    'summary': 'Automated appointment reminders, recall campaigns and patient communication log via email and SMS.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
        'mail',
    ],
    'data': [
        'data/email_templates.xml',
        'data/cron_jobs.xml',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Communication & Reminders\n=================================\nKeep patients informed and reduce no-shows with automated multi-channel communication.\n\nFeatures\n--------\n- Appointment reminders: 24-hour and 2-hour before, via email and/or SMS\n- Recall campaigns — contact patients due for 6-month check-up\n- Birthday greetings (optional)\n- Communication log on patient record showing every message sent\n- Configurable message templates with patient name, date and dentist merge fields\n- Unsubscribe / opt-out tracking\n- Manual send option from the appointment form\n\nIntegrates with Dental Telegram Reminders and Dental WhatsApp Reminders for additional channels.\n',
    'price': 0,
    'currency': 'USD',
}
