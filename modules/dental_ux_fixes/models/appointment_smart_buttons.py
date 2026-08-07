from odoo import api, fields, models


class DentalAppointmentSmartButtons(models.Model):
    _inherit = 'dental.appointment'

    # ── Calendar slot display ────────────────────────────────────────────────
    # Odoo 18 calendar uses display_name as the event card title.
    # Override to show "Patient | Dentist" instead of APT/08023.

    @api.depends('patient_id', 'dentist_id', 'appointment_no')
    def _compute_display_name(self):
        for apt in self:
            parts = []
            if apt.patient_id:
                parts.append(apt.patient_id.name)
            if apt.dentist_id:
                parts.append(apt.dentist_id.name)
            ref = apt.appointment_no or 'New'
            if parts:
                apt.display_name = ref + ' | ' + ' | '.join(parts)
            else:
                apt.display_name = ref

    # ── Smart button counts ──────────────────────────────────────────────────

    tooth_record_count = fields.Integer(
        string='Dental Chart',
        compute='_compute_tooth_record_count',
    )
    claim_count = fields.Integer(
        string='Claims',
        compute='_compute_claim_count',
    )
    prescription_count = fields.Integer(
        string='Prescriptions',
        compute='_compute_prescription_count',
    )

    @api.depends('patient_id')
    def _compute_tooth_record_count(self):
        """Count tooth records for the appointment's patient."""
        ToothRecord = self.env['dental.tooth.record']
        for apt in self:
            if apt.patient_id:
                apt.tooth_record_count = ToothRecord.search_count(
                    [('patient_id', '=', apt.patient_id.id)])
            else:
                apt.tooth_record_count = 0

    @api.depends()
    def _compute_claim_count(self):
        """Count insurance claims filed against this appointment."""
        Claim = self.env['dental.claim']
        for apt in self:
            apt.claim_count = Claim.search_count(
                [('appointment_id', '=', apt.id)])

    @api.depends()
    def _compute_prescription_count(self):
        """Count prescriptions linked to this appointment."""
        Rx = self.env['dental.prescription']
        for apt in self:
            apt.prescription_count = Rx.search_count(
                [('appointment_id', '=', apt.id)])

    def action_view_dental_chart(self):
        self.ensure_one()
        view = self.env.ref('dental_charting_pro.view_partner_form_dental_chart')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dental Chart',
            'res_model': 'res.partner',
            'res_id': self.patient_id.id,
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'target': 'current',
            # Picked up by the odontogram widget's saveBatch() so records
            # created from inside an appointment auto-fill the treating
            # doctor / appointment link, and the treatment when the
            # appointment has exactly one (ambiguous with several, so left
            # blank for the dentist to choose manually in that case).
            'context': {
                'default_appointment_id': self.id,
                'default_doctor_id': self.dentist_id.id,
                'default_treatment_id': (
                    self.treatments[0].id if len(self.treatments) == 1 else False),
            },
        }

    def action_view_claims(self):
        """Open claims list for this appointment; create new if none yet."""
        self.ensure_one()
        claims = self.env['dental.claim'].search(
            [('appointment_id', '=', self.id)])
        if len(claims) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Insurance Claim',
                'res_model': 'dental.claim',
                'view_mode': 'form',
                'res_id': claims.id,
            }
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Insurance Claims',
            'res_model': 'dental.claim',
            'view_mode': 'list,form',
            'domain': [('appointment_id', '=', self.id)],
            'context': {
                'default_patient_id': self.patient_id.id,
                'default_appointment_id': self.id,
            },
        }
        if not claims:
            action['view_mode'] = 'form'
            action.pop('domain', None)
        return action

    def action_view_prescriptions(self):
        """Open prescriptions for this appointment; pre-fill context for new ones."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Prescriptions',
            'res_model': 'dental.prescription',
            'view_mode': 'list,form',
            'domain': [('appointment_id', '=', self.id)],
            'context': {
                'default_appointment_id': self.id,
                'default_patient_id': self.patient_id.id,
            },
        }
