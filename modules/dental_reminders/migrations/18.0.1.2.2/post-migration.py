def migrate(cr, version):
    """v1.2.2: Telegram linking now uses one-time tokens, not patient numbers.

    The patient_not_found template is noupdate, so refresh its body only
    if the clinic never edited it (still the shipped default text).
    """
    cr.execute("""
        UPDATE dental_telegram_template
           SET body = %s
         WHERE template_key = 'patient_not_found'
           AND body = %s
    """, (
        'رابط التفعيل غير صالح أو مستخدم مسبقاً — يرجى طلب رابط جديد من '
        'الاستقبال. / This link is invalid or already used, please ask '
        'reception for a new one.',
        'لم نتمكن من العثور على رقم المريض {patient_no} — يرجى مراجعة '
        'الاستقبال. / Patient number {patient_no} not found, please contact '
        'reception.',
    ))
