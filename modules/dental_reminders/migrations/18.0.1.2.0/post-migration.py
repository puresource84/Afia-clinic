def migrate(cr, version):
    """v1.2: offset_direction column + per-template log dedupe.

    1. Review-request templates existed before the direction field —
       their semantic was always AFTER the visit.
    2. The crons now dedupe via the message log instead of the legacy
       review_sent / tg_reminder_sent booleans. Backfill log rows for
       recently-flagged appointments so the upgrade does not re-send
       messages that the booleans already recorded.
    """
    cr.execute("""
        UPDATE dental_telegram_template
           SET offset_direction = 'after'
         WHERE template_key = 'review_request'
    """)
    cr.execute("""
        UPDATE dental_telegram_template
           SET offset_direction = 'before'
         WHERE offset_direction IS NULL
    """)
    # Backfill: review requests already sent (boolean) within the lookback
    # window of the new scheduler (yesterday/today + day-offset targets).
    cr.execute("""
        INSERT INTO dental_telegram_message_log
            (appointment_id, patient_id, template_id, template_key,
             body, sent_date, is_test)
        SELECT a.id, a.patient_id, t.id, t.template_key,
               '(backfilled from review_sent flag at v1.2 upgrade)',
               now() at time zone 'UTC', false
          FROM dental_appointment a
          JOIN dental_telegram_template t
            ON t.template_key = 'review_request'
         WHERE a.review_sent = true
           AND a.appointment_date >= (current_date - interval '7 days')
           AND NOT EXISTS (SELECT 1 FROM dental_telegram_message_log l
                            WHERE l.appointment_id = a.id
                              AND l.template_id = t.id
                              AND l.is_test = false)
    """)
    cr.execute("""
        INSERT INTO dental_telegram_message_log
            (appointment_id, patient_id, template_id, template_key,
             body, sent_date, is_test)
        SELECT a.id, a.patient_id, t.id, t.template_key,
               '(backfilled from tg_reminder_sent flag at v1.2 upgrade)',
               now() at time zone 'UTC', false
          FROM dental_appointment a
          JOIN dental_telegram_template t
            ON t.template_key = 'reminder'
         WHERE a.tg_reminder_sent = true
           AND a.appointment_date >= current_date
           AND NOT EXISTS (SELECT 1 FROM dental_telegram_message_log l
                            WHERE l.appointment_id = a.id
                              AND l.template_id = t.id
                              AND l.is_test = false)
    """)
