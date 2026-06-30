import logging
from datetime import timedelta

import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)

TIMEOUT = 15


class ResConfigSettingsWhatsApp(models.TransientModel):
    _inherit = 'res.config.settings'

    dental_wa_api_url = fields.Char(
        string='WhatsApp Gateway URL',
        config_parameter='dental_whatsapp.api_url',
        help='HTTP endpoint of the WhatsApp Business API / gateway '
             '(e.g. https://graph.facebook.com/v19.0/<phone_id>/messages).')
    dental_wa_api_token = fields.Char(
        string='WhatsApp API Token',
        config_parameter='dental_whatsapp.api_token')


class DentalAppointmentWhatsApp(models.Model):
    _inherit = 'dental.appointment'

    wa_reminder_sent = fields.Boolean(
        string='WhatsApp Reminder Sent', default=False, copy=False)

    # ------------------------------------------------------------------
    # Gateway
    # ------------------------------------------------------------------
    def _wa_get_config(self):
        icp = self.env['ir.config_parameter'].sudo()
        return icp.get_param('dental_whatsapp.api_url'), icp.get_param(
            'dental_whatsapp.api_token')

    def _wa_send(self, phone, body):
        """Send one WhatsApp text message through the configured gateway.

        Returns True on success. Never raises — reminder crons must not abort.
        """
        url, token = self._wa_get_config()
        if not (url and token and phone):
            return False
        phone = ''.join(ch for ch in phone if ch.isdigit() or ch == '+')
        payload = {
            'messaging_product': 'whatsapp',
            'to': phone,
            'type': 'text',
            'text': {'body': body},
        }
        try:
            resp = requests.post(
                url, json=payload, timeout=TIMEOUT,
                headers={'Authorization': 'Bearer %s' % token})
            if resp.status_code in (200, 201):
                return True
            _logger.warning('WhatsApp gateway returned %s: %s',
                            resp.status_code, resp.text[:500])
        except Exception as exc:  # noqa: BLE001 — cron must survive
            _logger.warning('WhatsApp send failed for %s: %s', phone, exc)
        return False

    # ------------------------------------------------------------------
    # Crons
    # ------------------------------------------------------------------
    def _cron_send_whatsapp_reminders(self):
        """WhatsApp reminder for appointments scheduled tomorrow."""
        tomorrow = fields.Date.today() + timedelta(days=1)
        appointments = self.search([
            ('appointment_date', '=', tomorrow),
            ('state', 'in', ('confirmed', 'in_progress')),
            ('wa_reminder_sent', '=', False),
        ])
        sent = 0
        for apt in appointments:
            patient = apt.patient_id
            phone = patient.mobile or patient.phone
            if not phone:
                continue
            body = self._wa_reminder_body(apt)
            if self._wa_send(phone, body):
                apt.wa_reminder_sent = True
                apt.message_post(body='WhatsApp reminder sent to %s' % phone)
                sent += 1
        _logger.info('WhatsApp appointment reminders sent: %d', sent)

    def _wa_reminder_body(self, apt):
        patient = apt.patient_id
        clinic = self.env.company.name
        date_str = fields.Date.to_string(apt.appointment_date)
        return (
            'Hello %(name)s, this is a reminder of your dental appointment '
            'at %(clinic)s on %(date)s. Reply CONFIRM to confirm or call us '
            'to reschedule. / مرحباً %(name)s، نذكّركم بموعدكم في عيادة '
            '%(clinic)s بتاريخ %(date)s. يرجى الرد بكلمة تأكيد أو الاتصال '
            'بنا لإعادة الجدولة.'
        ) % {'name': patient.name, 'clinic': clinic, 'date': date_str}
