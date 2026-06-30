from odoo import api, fields, models


class ResPartnerDentalButtons(models.Model):
    _inherit = 'res.partner'

    appointment_count = fields.Integer(
        string='Appointments',
        compute='_compute_appointment_count',
    )

    @api.depends()
    def _compute_appointment_count(self):
        Apt = self.env['dental.appointment']
        for partner in self:
            partner.appointment_count = Apt.search_count(
                [('patient_id', '=', partner.id)]) if partner.id else 0

    def action_view_appointments(self):
        """Open this patient's appointments; offer New Appointment from there."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'res_model': 'dental.appointment',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {
                'default_patient_id': self.id,
                'search_default_patient_id': self.id,
            },
        }

    def action_new_appointment(self):
        """Jump straight to a blank new appointment pre-filled with patient."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Appointment',
            'res_model': 'dental.appointment',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_patient_id': self.id},
        }

    def action_telegram_link(self):
        """Open the patient's Telegram bot deep link in a new tab.

        Reception staff can share this URL (or its QR) with the patient so
        they self-link their chat — no manual entry needed.
        """
        self.ensure_one()
        Param = self.env['ir.config_parameter'].sudo()
        bot_username = Param.get_param('dental_telegram.bot_username', '')
        patient_no = getattr(self, 'patient_no', '') or ''

        if not bot_username:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Telegram not configured',
                    'message': 'Set the bot username in Settings → Clinic Core → Telegram.',
                    'type': 'warning',
                    'sticky': False,
                },
            }
        if not patient_no:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No patient number',
                    'message': 'Save the patient record first to assign a patient number.',
                    'type': 'warning',
                    'sticky': False,
                },
            }
        url = 'https://t.me/%s?start=%s' % (
            bot_username.lstrip('@'), patient_no)
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'new'}
