from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AppointmentCancelWizard(models.TransientModel):
    """Wizard to collect a mandatory cancellation reason before marking
    an appointment as cancelled in the Patient Flow board."""
    _name = 'appointment.cancel.wizard'
    _description = 'Cancel Appointment — Reason Required'

    appointment_id = fields.Many2one(
        'dental.appointment',
        string='Appointment',
        required=True,
        readonly=True,
    )
    # Regular fields populated via default_get — avoids the Odoo 18 issue
    # where related fields on readonly Many2one don't render in new wizard records.
    patient_name = fields.Char(
        string='Patient',
        readonly=True,
    )
    appointment_date = fields.Date(
        string='Date',
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # In Odoo 18, default_* context keys may not appear in res yet —
        # fall back to reading the context directly.
        apt_id = res.get('appointment_id') or self._context.get('default_appointment_id')
        if apt_id:
            apt = self.env['dental.appointment'].browse(apt_id)
            res['patient_name'] = apt.patient_id.name or ''
            res['appointment_date'] = apt.appointment_date
        return res

    reason = fields.Text(
        string='Cancellation Reason',
        required=True,
        help='Describe why the appointment is being cancelled.',
    )

    @api.constrains('reason')
    def _check_reason_not_empty(self)