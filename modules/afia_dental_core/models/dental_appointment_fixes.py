from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DentalAppointmentFixes(models.Model):
    _inherit = 'dental.appointment'

    @api.constrains('state', 'apt_start')
    def _check_booking_time_on_confirm(self):
        """Block Confirm if no Start Time is set (scheduling guard).

        Does NOT block In Progress — action_start_treatment auto-stamps now().
        """
        for apt in self:
            if apt.state == 'confirmed' and not apt.apt_start:
                raise ValidationError(_(
                    'Please set a Start Time before confirming '
                    'appointment %s.') % (apt.appointment_no or 'new'))

    def action_start_treatment(self):
        """Confirmed -> In Progress: stamp actual session start time."""
        for apt in self:
            if apt.state == 'confirmed':
                apt.write({
                    'state': 'in_progress',
                    'apt_start': fields.Datetime.now(),
                })

    def action_done(self):
        """In Progress -> Done: stamp actual session end time, then super()."""
        now = fields.Datetime.now()
        for apt in self:
            if not apt.apt_end:
                apt.apt_end = now
        return super().action_done()
