from odoo import models


class ResPartnerDentalButtons(models.Model):
    _inherit = 'res.partner'

    # appointment_count field + _compute_appointment_count() +
    # action_view_appointments() used to be redefined here as well,
    # shadowing afia_dental_core's originals (this module loads after
    # afia_dental_core, so this copy silently won at runtime). That
    # duplication is fixed 2026-09-20 — see
    # afia_dental_core/.spec/bugs/afia_dental_core-duplicate-appointment-button/.
    # The single remaining implementation of both lives in
    # afia_dental_core/models/res_partner.py; this module keeps only the
    # two actions genuinely unique to it below.

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
        url = self._tg_deep_link()
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'new'}
