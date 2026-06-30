from odoo import models, fields, api
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class DentalAppointmentComm(models.Model):
    _inherit = 'dental.appointment'

    reminder_sent = fields.Boolean(string='Reminder Sent', default=False, copy=False)
    recall_due_date = fields.Date(string='Recall Due Date')

    def _cron_send_appointment_reminders(self):
        """Send email reminders for appointments scheduled tomorrow."""
        tomorrow = fields.Date.today() + timedelta(days=1)
        appointments = self.search([
            ('appointment_date', '=', tomorrow),
            ('state', 'in', ('confirmed', 'in_progress')),
            ('reminder_sent', '=', False),
        ])
        template = self.env.ref(
            'dental_communication.email_template_appointment_reminder',
            raise_if_not_found=False)
        for apt in appointments:
            if template and apt.patient_id.email:
                try:
                    template.send_mail(apt.id, force_send=True)
                    apt.reminder_sent = True
                except Exception as e:
                    _logger.warning('Reminder failed for appointment %s: %s', apt.id, e)
        _logger.info('Appointment reminders sent: %d', len(appointments))

    def _cron_send_recall_notices(self):
        """Send recall email to patients whose recall_due_date is today."""
        today = fields.Date.today()
        appointments = self.search([
            ('recall_due_date', '=', today),
            ('state', '=', 'done'),
        ])
        template = self.env.ref(
            'dental_communication.email_template_patient_recall',
            raise_if_not_found=False)
        for apt in appointments:
            if template and apt.patient_id.email:
                try:
                    template.send_mail(apt.id, force_send=True)
                except Exception as e:
                    _logger.warning('Recall notice failed for appointment %s: %s', apt.id, e)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.appointment_date and not rec.recall_due_date:
                from dateutil.relativedelta import relativedelta
                rec.recall_due_date = rec.appointment_date + relativedelta(months=6)
        return records