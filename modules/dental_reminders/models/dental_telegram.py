import logging
import secrets
from datetime import timedelta

import pytz
import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)

TIMEOUT = 15
TG_API = 'https://api.telegram.org/bot%s/%s'

CONFIRM_WORDS = {'confirm', 'yes', 'ok', 'تأكيد', 'تاكيد', 'نعم', 'اوكي'}
CANCEL_WORDS = {'cancel', 'no', 'الغاء', 'إلغاء', 'لا'}


class ResConfigSettingsTelegram(models.TransientModel):
    _inherit = 'res.config.settings'

    dental_tg_enabled = fields.Boolean(
        string='Enable Telegram',
        config_parameter='dental_telegram.enabled',
        help='Master switch for Telegram reminders and patient linking.')
    dental_tg_bot_token = fields.Char(
        string='Telegram Bot Token',
        config_parameter='dental_telegram.bot_token',
        help='Token from @BotFather (e.g. 123456:ABC-DEF...).')
    dental_tg_bot_username = fields.Char(
        string='Bot Username',
        config_parameter='dental_telegram.bot_username',
        help='Without @. Used to build patient deep links: t.me/<bot>?start=<link token>')
    dental_tg_recall_months = fields.Integer(
        string='Recall After (months)', default=6,
        config_parameter='dental_telegram.recall_months',
        help='Hygiene recall interval set automatically when an appointment is done.')
    dental_tg_review_link = fields.Char(
        string='Review Link (Google Maps)',
        config_parameter='dental_telegram.review_link',
        help='Sent to patients who rate their visit 5/5.')
    dental_tg_clinic_tz = fields.Char(
        string='Clinic Timezone', default='Asia/Baghdad',
        config_parameter='dental_telegram.clinic_tz')


class ResPartnerTelegram(models.Model):
    _inherit = 'res.partner'

    telegram_chat_id = fields.Char(
        string='Telegram Chat ID', copy=False,
        help='Filled automatically when the patient opens the clinic bot '
             'deep link (t.me/<bot>?start=<link token>).')
    # Random, single-use code put in the deep link instead of the patient
    # number: patient numbers are sequential (PAT/00001), so anyone could
    # have linked their own chat to another patient and received (or
    # cancelled) that patient's appointments.
    telegram_link_token = fields.Char(
        string='Telegram Link Token', copy=False, groups='base.group_user')

    def _tg_get_link_token(self):
        self.ensure_one()
        if not self.telegram_link_token:
            self.sudo().telegram_link_token = secrets.token_urlsafe(16)
        return self.telegram_link_token

    def _tg_deep_link(self):
        """Return the t.me deep link for this patient, or '' if the bot
        username is not configured."""
        self.ensure_one()
        bot = (self.env['ir.config_parameter'].sudo().get_param(
            'dental_telegram.bot_username') or '').lstrip('@')
        if not bot:
            return ''
        return 'https://t.me/%s?start=%s' % (bot, self._tg_get_link_token())

    @staticmethod
    def _tg_consume_link_token(env, code):
        """Find the patient owning ``code`` and burn the token so a leaked
        card or link cannot be reused to hijack the chat later."""
        if not code:
            return env['res.partner']
        patient = env['res.partner'].sudo().search([
            ('is_patient', '=', True),
            ('telegram_link_token', '=', code)], limit=1)
        if patient:
            patient.telegram_link_token = False
        return patient


class DentalAppointmentTelegram(models.Model):
    _inherit = 'dental.appointment'

    tg_reminder_sent = fields.Boolean(
        string='Telegram Reminder Sent', default=False, copy=False)
    tg_recall_sent = fields.Boolean(
        string='Telegram Recall Sent', default=False, copy=False)
    review_sent = fields.Boolean(
        string='Review Request Sent', default=False, copy=False)
    review_score = fields.Integer(string='Review Score', copy=False)
    recall_due_date = fields.Date(
        string='Recall Due Date', copy=False,
        help='Date when the patient is due for their next hygiene recall. '
             'Set automatically when the appointment is marked Done.')

    # ------------------------------------------------------------------
    # Config / helpers
    # ------------------------------------------------------------------
    def _tg_param(self, key, default=''):
        return self.env['ir.config_parameter'].sudo().get_param(
            'dental_telegram.' + key, default)

    def _tg_enabled(self):
        return self._tg_param('enabled')

    def _tg_token(self):
        if not self._tg_enabled():
            return None
        return self._tg_param('bot_token')

    def _clinic_today(self):
        """NOW-bucket E2: date math in CLINIC timezone, not UTC."""
        try:
            tz = pytz.timezone(self._tg_param('clinic_tz', 'Asia/Baghdad'))
        except pytz.UnknownTimeZoneError:
            tz = pytz.utc
        return pytz.utc.localize(fields.Datetime.now()).astimezone(tz).date()

    # ------------------------------------------------------------------
    # Bot API
    # ------------------------------------------------------------------
    def _tg_call(self, method, payload):
        token = self._tg_token()
        if not token:
            return None
        try:
            resp = requests.post(
                TG_API % (token, method), json=payload, timeout=TIMEOUT)
            data = resp.json()
            if data.get('ok'):
                return data.get('result')
            _logger.warning('Telegram %s failed: %s', method, str(data)[:300])
        except Exception as exc:  # noqa: BLE001
            _logger.warning('Telegram %s error: %s', method, exc)
        return None

    def _tg_send(self, chat_id, body):
        return self._tg_call('sendMessage', {
            'chat_id': chat_id, 'text': body}) is not None

    # ------------------------------------------------------------------
    # Inbound: linking, confirm/cancel, review scores
    # ------------------------------------------------------------------
    def _cron_poll_telegram_updates(self):
        if not self._tg_enabled():
            return
        icp = self.env['ir.config_parameter'].sudo()
        offset = int(icp.get_param('dental_telegram.last_update_id', '0'))
        updates = self._tg_call('getUpdates', {
            'offset': offset + 1, 'timeout': 0,
            'allowed_updates': ['message']}) or []
        for upd in updates:
            offset = max(offset, upd.get('update_id', 0))
            msg = upd.get('message') or {}
            text = (msg.get('text') or '').strip()
            chat_id = str((msg.get('chat') or {}).get('id') or '')
            if not (chat_id and text):
                continue
            if text.lower().startswith('/start'):
                self._tg_handle_start(chat_id, text)
            else:
                self._tg_handle_reply(chat_id, text)
        icp.set_param('dental_telegram.last_update_id', str(offset))

    def _tg_handle_start(self, chat_id, text):
        Partner = self.env['res.partner'].sudo()
        parts = text.split(maxsplit=1)
        code = parts[1].strip() if len(parts) > 1 else ''
        patient = Partner._tg_consume_link_token(self.env, code)
        if patient:
            patient.telegram_chat_id = chat_id
            self._tg_send(chat_id, (
                'تم ربط حسابك بنجاح! ستصلك تذكيرات مواعيدك هنا. / '
                'Linked successfully, %s. Your appointment reminders '
                'will arrive here.') % patient.name)
        elif code:
            self._tg_send(chat_id, (
                'رابط التفعيل غير صالح أو مستخدم مسبقاً — يرجى طلب رابط '
                'جديد من الاستقبال. / This link is invalid or already '
                'used, please ask reception for a new one.'))

    def _tg_handle_reply(self, chat_id, text):
        """NOW-bucket C1 + C3: CONFIRM / CANCEL / review score replies."""
        patient = self.env['res.partner'].sudo().search(
            [('telegram_chat_id', '=', chat_id)], limit=1)
        if not patient:
            return
        word = text.strip().lower()
        today = self._clinic_today()
        if word in CONFIRM_WORDS or word in CANCEL_WORDS:
            apt = self.sudo().search([
                ('patient_id', '=', patient.id),
                ('appointment_date', '>=', today),
                ('state', 'in', ('draft', 'confirmed')),
            ], order='appointment_date asc', limit=1)
            if not apt:
                self._tg_send(chat_id,
                              'لا يوجد موعد قادم مسجل. / No upcoming '
                              'appointment found.')
                return
            if word in CONFIRM_WORDS:
                if apt.state == 'draft':
                    try:
                        apt.action_confirm()
                    except Exception:  # noqa: BLE001 — e.g. no shift set
                        pass
                apt.message_post(body='Patient CONFIRMED via Telegram.')
                self._tg_send(chat_id, (
                    'تم تأكيد موعدك بتاريخ %s. شكراً لك! / Your appointment '
                    'on %s is confirmed. Thank you!') % (
                        apt.appointment_date, apt.appointment_date))
            else:
                apt.action_cancel()
                apt.message_post(body='Patient CANCELLED via Telegram.')
                self._tg_send(chat_id, (
                    'تم إلغاء موعدك بتاريخ %s. للحجز مجدداً يرجى الاتصال '
                    'بالعيادة. / Your appointment on %s was cancelled. '
                    'Call us to rebook.') % (
                        apt.appointment_date, apt.appointment_date))
        elif word.isdigit() and 1 <= int(word) <= 5:
            score = int(word)
            apt = self.sudo().search([
                ('patient_id', '=', patient.id),
                ('review_sent', '=', True),
                ('review_score', '=', 0),
            ], order='appointment_date desc', limit=1)
            if not apt:
                return
            apt.review_score = score
            apt.message_post(body='Patient review via Telegram: %d/5' % score)
            if score == 5 and self._tg_param('review_link'):
                self._tg_send(chat_id, (
                    'شكراً جزيلاً! يسعدنا تقييمك على خرائط جوجل: %s / '
                    'Thank you! We would love a Google review: %s') % (
                        self._tg_param('review_link'),
                        self._tg_param('review_link')))
            else:
                self._tg_send(chat_id,
                              'شكراً لملاحظاتك، سنعمل على التحسين. / '
                              'Thank you for your feedback.')
                if score <= 3:
                    apt.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary='Low patient review (%d/5) — follow up'
                                % score,
                        user_id=self.env.ref('base.user_admin').id)

    # ------------------------------------------------------------------
    # Outbound crons
    # ------------------------------------------------------------------
    def _cron_send_telegram_reminders(self):
        if not self._tg_enabled():
            return
        tomorrow = self._clinic_today() + timedelta(days=1)
        appointments = self.search([
            ('appointment_date', '=', tomorrow),
            ('state', 'in', ('confirmed', 'in_progress')),
            ('tg_reminder_sent', '=', False),
        ])
        sent = 0
        for apt in appointments:
            chat_id = apt.patient_id.telegram_chat_id
            if chat_id and self._tg_send(chat_id, self._tg_reminder_body(apt)):
                apt.tg_reminder_sent = True
                apt.message_post(body='Telegram reminder sent.')
                sent += 1
        _logger.info('Telegram appointment reminders sent: %d', sent)

    def _cron_send_review_requests(self):
        """NOW-bucket C3: day-after review request."""
        if not self._tg_enabled():
            return
        yesterday = self._clinic_today() - timedelta(days=1)
        appointments = self.search([
            ('appointment_date', '=', yesterday),
            ('state', '=', 'done'),
            ('review_sent', '=', False),
        ])
        for apt in appointments:
            chat_id = apt.patient_id.telegram_chat_id
            if chat_id and self._tg_send(chat_id, (
                    'مرحباً %s، كيف كانت زيارتك للعيادة أمس؟ قيّمنا برقم من '
                    '1 إلى 5. / Hi %s, how was your visit yesterday? Rate us '
                    '1 to 5.') % (apt.patient_id.name, apt.patient_id.name)):
                apt.review_sent = True

    def _cron_send_telegram_recalls(self):
        """NOW-bucket A7: hygiene recall campaign over Telegram."""
        if not self._tg_enabled():
            return
        today = self._clinic_today()
        appointments = self.search([
            ('recall_due_date', '=', today),
            ('state', '=', 'done'),
            ('tg_recall_sent', '=', False),
        ])
        for apt in appointments:
            chat_id = apt.patient_id.telegram_chat_id
            if chat_id and self._tg_send(chat_id, (
                    'مرحباً %s، حان موعد فحصك وتنظيفك الدوري في عيادة %s! '
                    'يرجى الاتصال بنا أو الرد بكلمة "حجز" لتحديد موعد. / '
                    'Hi %s, you are due for your periodic check-up at %s. '
                    'Call us to book.') % (
                        apt.patient_id.name, self.env.company.name,
                        apt.patient_id.name, self.env.company.name)):
                apt.tg_recall_sent = True
                apt.message_post(body='Telegram recall sent.')

    # ------------------------------------------------------------------
    # Recall auto-scheduling
    # ------------------------------------------------------------------
    def action_done(self):
        res = super().action_done()
        months = int(self._tg_param('recall_months', '6') or 6)
        for apt in self:
            if hasattr(apt, 'recall_due_date') and not apt.recall_due_date:
                apt.recall_due_date = self._clinic_today() + timedelta(
                    days=30 * months)
        return res

    def _tg_reminder_body(self, apt):
        patient = apt.patient_id
        clinic = self.env.company.name
        date_str = fields.Date.to_string(apt.appointment_date)
        shift = apt.shift_id.name or ''
        return (
            'مرحباً %(name)s، نذكّركم بموعدكم في عيادة %(clinic)s بتاريخ '
            '%(date)s %(shift)s.\nللتأكيد أرسل "تأكيد"، وللإلغاء أرسل '
            '"الغاء".\nHello %(name)s, reminder of your dental appointment '
            'at %(clinic)s on %(date)s %(shift)s. Reply CONFIRM or CANCEL.'
        ) % {'name': patient.name, 'clinic': clinic,
             'date': date_str, 'shift': shift}
