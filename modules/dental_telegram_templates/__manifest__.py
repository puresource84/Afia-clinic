{
    'name': 'Dental Telegram Templates',
    'version': '18.0.1.2.2',
    'category': 'Healthcare/Dental',
    'summary': 'Editable Telegram message templates for every patient notification — bilingual, with merge fields.',
    'description': 'Dental Telegram Message Templates\n==================================\nCentralised configuration for all Telegram messages sent to patients.\n\nConfigurable Templates\n----------------------\n- Appointment confirmation\n- 24-hour reminder\n- 2-hour reminder\n- Appointment cancellation notice\n- Recall / check-up due\n- Lab work ready\n- Invoice issued\n- General clinic notification\n\nFeatures\n--------\n- Bilingual templates (Arabic + English) — patient language auto-selected\n- Merge field picker: {patient_name}, {appointment_date}, {dentist_name}, {clinic_name}, etc.\n- Live preview before saving\n- Template versioning — revert to a previous version\n- Per-template enable / disable toggle\n- Emoji support\n\nRequires: dental_reminders_telegram\n',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_reminders_telegram',
        'clinic_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/telegram_templates.xml',
        'views/telegram_template_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
    'price': 0,
    'currency': 'USD',
}
