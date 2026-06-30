{
    'name': 'Dental WhatsApp Reminders',
    'version': '18.0.1.0.0',
    'category': 'Healthcare/Dental',
    'summary': 'Appointment reminders and recall notices over WhatsApp via gateway API — no WhatsApp Business API account needed.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_communication',
    ],
    'data': [
        'data/cron_jobs.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental WhatsApp Reminders\n=========================\nSend appointment reminders to patients via WhatsApp using a third-party gateway API.\n\nSupported Gateways\n------------------\n- UltraMsg\n- ChatAPI\n- Any gateway with a REST POST endpoint (configurable)\n\nFeatures\n--------\n- 24-hour and 2-hour pre-appointment reminders\n- Patient recall messages\n- Bilingual message templates (Arabic / English)\n- Delivery status polling (where supported by gateway)\n- Opt-out / unsubscribe management\n- Manual send from appointment form\n- Bulk send for recall campaigns\n- Message log per patient\n\nConfigure the gateway URL and token in Settings → Dental → WhatsApp.\n',
    'price': 0,
    'currency': 'USD',
}
