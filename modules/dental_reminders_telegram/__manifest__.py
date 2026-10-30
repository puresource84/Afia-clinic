{
    'name': 'Dental Telegram Reminders',
    'version': '18.0.1.0.1',
    'category': 'Healthcare/Dental',
    'summary': 'Appointment reminders over Telegram bot with patient deep-link setup, bilingual messages and delivery tracking.',
    'description': 'Dental Telegram Reminders\n=========================\nSend appointment reminders and recall messages to patients via Telegram.\n\nSetup\n-----\n1. Create a Telegram bot via @BotFather and add the token in Odoo settings\n2. Patients link their Telegram account with a one-time deep link sent by the clinic\n3. Reminders are sent automatically once linked\n\nFeatures\n--------\n- 24-hour and 2-hour pre-appointment reminders\n- Recall message for patients overdue a check-up\n- Bilingual messages: Arabic and English based on patient language preference\n- Delivery status tracking (sent / delivered / read)\n- Fallback to SMS if Telegram is not linked\n- Manual send button on the appointment form\n- Configurable message templates (see Dental Telegram Templates module)\n',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
        'clinic_core',
    ],
    'data': [
        'data/cron_jobs.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'reports/telegram_card_report.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'price': 0,
    'currency': 'USD',
}
