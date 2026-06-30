from . import models


def post_init_hook(env):
    """Tighten cron cadence for template-based timing:
    - recall daily → hourly (earliest-hour gate delivers day-of)
    - reminders hourly → every 10 min (hour-before windows need it)"""
    recall = env.ref('dental_reminders_telegram.cron_telegram_recalls',
                     raise_if_not_found=False)
    if recall:
        recall.write({'interval_number': 1, 'interval_type': 'hours'})
    reminders = env.ref('dental_reminders_telegram.cron_telegram_reminders',
                        raise_if_not_found=False)
    if reminders:
        reminders.write({'interval_number': 10, 'interval_type': 'minutes'})
