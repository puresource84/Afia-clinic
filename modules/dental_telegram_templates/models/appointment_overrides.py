"""Wire dental_reminders_telegram's hardcoded messages through the
editable template table, with multi-stage reminder support (offsets in
days AND hours before the appointment). Every template lookup falls back
to the original built-in text when the template is missing or inactive."""
import logging
from datetime import datetime, time as dtime, timedelta

import pytz

from odoo import fields, models

_logger = logging.getLogger(__name__)

CONFIRM_WORDS = {'confirm', 'yes', 'ok', 'تأكيد', 'تاكيد', 'نعم', 'اوكي'}
CANCEL_WORDS = {'cancel', 'no', 'الغاء', 'إلغاء', 'لا'}


def _float_to_hhmm(value):
    if value is None or value is False:
        return ''
    hours = int(value)
    minutes = int(round((value - hours) * 60))
    if minutes == 60:
        hours, minutes = hours + 1, 0
    return '%02d:%02d' % (hours, minutes)


class DentalAppointmentTgTemplates(models.Model):
    _inherit = 'dental.appointment'

    # ------------------------------------------------------------------
    # Clinic-timezone helpers
    # ------------------------------------------------------------------
    def _clinic_tz(self):
        try:
            return pytz.timezone(self._tg_param('clinic_tz', 'Asia/Baghdad'))
        except pytz.UnknownTimeZoneError:
            return pytz.utc

    def _clinic_now(self):
        return pytz.utc.localize(fields.Datetime.now()).astimezone(
            self._clinic_tz())

    def _clinic_now_hour(self):
        now = self._clinic_now()
        return now.hour + now.minute / 60.0

    def _appointment_time_float(self, apt):
        """Time-of-day as float hours: online-booking slot first, else the
        shift start time. None when the appointment has no usable time."""
        slot = getattr(apt, 'booking_slot', 0.0) or 0.0
        if slot:
            return slot
        if apt.shift_id and apt.shift_id.start_time:
            return apt.shift_id.start_time
        return None

    def _appointment_datetime(self, apt):
        """Clinic-TZ aware datetime of the appointment, or None if the
        appointment has no time (hour-based reminders skip those)."""
        if not apt.appointment_date:
            return None
        hour_f = self._appointment_time_float(apt)
        if hour_f is None:
            return None
        hours = int(hour_f)
        minutes = int(round((hour_f - hours) * 60))
        if minutes == 60:
            hours, minutes = hours + 1, 0
        naive = datetime.combine(
            apt.appointment_date, dtime(min(hours, 23), min(minutes, 59)))
        return self._clinic_tz().localize(naive)

    # ------------------------------------------------------------------
    # Template context
    # ------------------------------------------------------------------
    def _tg_template_ctx(self, apt=None, patient=None):
        patient = patient or (apt and apt.patient_id)
        ctx = {
            'clinic_name': self.env.company.name,
            'review_link': self._tg_param('review_link') or '',
            'patient_name': patient and patient.name or '',
            'patient_no': patient and getattr(patient, 'patient_no', '') or '',
            'date': '', 'time': '', 'shift': '', 'dentist': '',
        }
        if apt:
            ctx.update({
                'date': fields.Date.to_string(apt.appointment_date) or '',
                'time': _float_to_hhmm(self._appointment_time_float(apt)),
                'shift': apt.shift_id and apt.shift_id.name or '',
                'dentist': apt.dentist_id and apt.dentist_id.name or '',
            })
        return ctx

    def _tg_text(self, key, fallback, apt=None, patient=None, extra=None):
        ctx = self._tg_template_ctx(apt=apt, patient=patient)
        if extra:
            ctx.update(extra)
        body = self.env['dental.telegram.template']._render_key(key, ctx)
        return body if body is not None else fallback

    def _tg_tmpls(self, key):
        return self.env['dental.telegram.template']._get(key)

    # ------------------------------------------------------------------
    # Outbound: generic timed-template scheduler
    # Every timed template supports the 4 combos:
    #   N hours before · N days before · N hours after · N days after
    # ------------------------------------------------------------------
    def _tg_reminder_body(self, apt):
        return self._tg_text('reminder', super()._tg_reminder_body(apt),
                             apt=apt)

    def _process_timed_templates(self, templates):
        """Send each active timed template exactly once per matching
        appointment (dedupe via the message log)."""
        Log = self.env['dental.telegram.message.log']
        now = self._clinic_now()
        today = now.date()
        sent = 0
        for tmpl in templates:
            offset = max(int(tmpl.offset_value or 0), 0) or 1
            before = tmpl.offset_direction != 'after'
            states = ('confirmed', 'in_progress') if before else ('done',)
            if tmpl.offset_unit == 'days':
                # day-based, gated by earliest send hour (clinic TZ)
                if self._clinic_now_hour() < (tmpl.send_after_hour or 0.0):
                    continue
                target = (today + timedelta(days=offset) if before
                          else today - timedelta(days=offset))
                candidates = self.search([
                    ('appointment_date', '=', target),
                    ('state', 'in', states),
                ])
            else:
                # hour-based: needs an appointment time; check a 2-day
                # date span and filter by the exact window below
                span = ([today, today + timedelta(days=1)] if before
                        else [today, today - timedelta(days=1)])
                candidates = self.search([
                    ('appointment_date', 'in', span),
                    ('state', 'in', states),
                ])
            for apt in candidates:
                if tmpl.offset_unit == 'hours':
                    apt_dt = self._appointment_datetime(apt)
                    if not apt_dt:
                        continue
                    if before:
                        # window: (visit − offset) … visit
                        if not (apt_dt - timedelta(hours=offset)
                                <= now < apt_dt):
                            continue
                    else:
                        # window: (visit + offset) … +24h (then expires)
                        start = apt_dt + timedelta(hours=offset)
                        if not (start <= now < start + timedelta(hours=24)):
                            continue
                chat_id = apt.patient_id.telegram_chat_id
                if not chat_id or Log._already_sent(apt, tmpl):
                    continue
                body = tmpl._render(self._tg_template_ctx(apt=apt))
                if self._tg_send(chat_id, body):
                    Log._log(tmpl, body, apt=apt)
                    if tmpl.template_key == 'reminder' and before \
                            and not apt.tg_reminder_sent:
                        apt.tg_reminder_sent = True  # legacy flag
                    if tmpl.template_key == 'review_request' \
                            and not apt.review_sent:
                        apt.review_sent = True  # enables score replies
                    apt.message_post(
                        body='Telegram message sent (%s).' % tmpl.name)
                    sent += 1
        if sent:
            _logger.info('Telegram timed messages sent: %d', sent)

    def _cron_send_telegram_reminders(self):
        templates = self._tg_tmpls('reminder')
        if not templates:
            return super()._cron_send_telegram_reminders()
        if not self._tg_enabled():
            return
        self._process_timed_templates(templates)

    def _cron_send_review_requests(self):
        templates = self._tg_tmpls('review_request')
        if not templates:
            return super()._cron_send_review_requests()
        if not self._tg_enabled():
            return
        self._process_timed_templates(templates)

    def _cron_send_telegram_recalls(self):
        tmpl = self._tg_tmpls('recall')[:1]
        if not tmpl:
            return super()._cron_send_telegram_recalls()
        if not self._tg_enabled():
            return
        if self._clinic_now_hour() < (tmpl.send_after_hour or 0.0):
            return
        Log = self.env['dental.telegram.message.log']
        today = self._clinic_today()
        appointments = self.search([
            ('recall_due_date', '=', today),
            ('state', '=', 'done'),
            ('tg_recall_sent', '=', False),
        ])
        for apt in appointments:
            chat_id = apt.patient_id.telegram_chat_id
            if not chat_id:
                continue
            body = tmpl._render(self._tg_template_ctx(apt=apt))
            if self._tg_send(chat_id, body):
                apt.tg_recall_sent = True
                Log._log(tmpl, body, apt=apt)
                apt.message_post(body='Telegram recall sent.')

    # ------------------------------------------------------------------
    # Inbound handlers (templated replies)
    # ------------------------------------------------------------------
    def _tg_handle_start(self, chat_id, text):
        Partner = self.env['res.partner'].sudo()
        parts = text.split(maxsplit=1)
        code = parts[1].strip() if len(parts) > 1 else ''
        patient = code and Partner.search(
            [('is_patient', '=', True), ('patient_no', '=', code)], limit=1)
        if patient:
            patient.telegram_chat_id = chat_id
            fallback = (
                'تم ربط حسابك بنجاح! ستصلك تذكيرات مواعيدك هنا. / '
                'Linked successfully, %s. Your appointment reminders '
                'will arrive here.') % patient.name
            self._tg_send(chat_id, self._tg_text(
                'welcome_linked', fallback, patient=patient))
        elif code:
            fallback = (
                'لم نتمكن من العثور على رقم المريض %s — يرجى مراجعة '
                'الاستقبال. / Patient number %s not found, please '
                'contact reception.') % (code, code)
            self._tg_send(chat_id, self._tg_text(
                'patient_not_found', fallback, extra={'patient_no': code}))

    def _tg_handle_reply(self, chat_id, text):
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
                self._tg_send(chat_id, self._tg_text(
                    'no_upcoming',
                    'لا يوجد موعد قادم مسجل. / No upcoming appointment '
                    'found.', patient=patient))
                return
            if word in CONFIRM_WORDS:
                if apt.state == 'draft':
                    try:
                        apt.action_confirm()
                    except Exception:  # noqa: BLE001 — e.g. no shift set
                        pass
                apt.message_post(body='Patient CONFIRMED via Telegram.')
                fallback = (
                    'تم تأكيد موعدك بتاريخ %s. شكراً لك! / Your appointment '
                    'on %s is confirmed. Thank you!') % (
                        apt.appointment_date, apt.appointment_date)
                self._tg_send(chat_id, self._tg_text(
                    'confirm_ack', fallback, apt=apt))
            else:
                apt.action_cancel()
                apt.message_post(body='Patient CANCELLED via Telegram.')
                fallback = (
                    'تم إلغاء موعدك بتاريخ %s. للحجز مجدداً يرجى الاتصال '
                    'بالعيادة. / Your appointment on %s was cancelled. '
                    'Call us to rebook.') % (
                        apt.appointment_date, apt.appointment_date)
                self._tg_send(chat_id, self._tg_text(
                    'cancel_ack', fallback, apt=apt))
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
                link = self._tg_param('review_link')
                fallback = (
                    'شكراً جزيلاً! يسعدنا تقييمك على خرائط جوجل: %s / '
                    'Thank you! We would love a Google review: %s') % (
                        link, link)
                self._tg_send(chat_id, self._tg_text(
                    'review_thanks_5', fallback, apt=apt))
            else:
                self._tg_send(chat_id, self._tg_text(
                    'review_thanks',
                    'شكراً لملاحظاتك، سنعمل على التحسين. / '
                    'Thank you for your feedback.', apt=apt))
                if score <= 3:
                    apt.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary='Low patient review (%d/5) — follow up'
                                % score,
                        user_id=self.env.ref('base.user_admin').id)
