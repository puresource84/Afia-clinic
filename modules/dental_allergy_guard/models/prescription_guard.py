from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DentalPrescriptionGuard(models.Model):
    _inherit = 'dental.prescription'

    allergy_override_reason = fields.Char(
        string='Allergy Override Reason', tracking=True, copy=False,
        help='Filling this allows saving DESPITE an allergy conflict '
             '(e.g. desensitisation completed, tolerance confirmed). '
             'The override is logged for audit.')
    patient_allergy_summary = fields.Text(
        compute='_compute_patient_allergy_summary',
        string='Patient Allergies')

    @api.depends('patient_id', 'patient_id.allergy_alert',
                 'patient_id.allergy_ids')
    def _compute_patient_allergy_summary(self):
        for rx in self:
            parts = []
            patient = rx.patient_id
            if patient:
                parts += ['%s (%s)' % (l.substance_id.name, l.severity)
                          for l in patient.allergy_ids]
                if patient.allergy_alert:
                    parts.append(patient.allergy_alert)
            rx.patient_allergy_summary = ' · '.join(parts)

    # ------------------------------------------------------------------
    # Hard stop
    # ------------------------------------------------------------------
    def _medicine_display_names(self):
        self.ensure_one()
        names = []
        for line in self.medicine_ids:
            label = ' '.join(filter(None, (
                line.medicament_id.name, line.generic_name)))
            if label:
                names.append(label)
        return names

    def _check_allergy_conflicts(self):
        """NOW-bucket A4: block prescriptions that conflict with patient
        allergies unless a clinician documents an override reason."""
        for rx in self:
            patient = rx.patient_id
            if not patient:
                continue
            conflicts = patient._allergy_conflicts_for(
                rx._medicine_display_names())
            if not conflicts:
                continue
            detail = '\n'.join('• %s ⟶ %s' % (med, sub)
                               for sub, med in conflicts)
            if rx.allergy_override_reason:
                rx.message_post(body=_(
                    '⚠ ALLERGY OVERRIDE by %(user)s — conflicts:\n%(detail)s\n'
                    'Reason: %(reason)s',
                    user=self.env.user.name, detail=detail,
                    reason=rx.allergy_override_reason))
                continue
            raise ValidationError(_(
                '⛔ ALLERGY HARD STOP — %(patient)s\n\n'
                'The prescription contains medicine(s) matching recorded '
                'allergies:\n%(detail)s\n\n'
                'Remove the medicine or, if clinically justified, fill '
                '"Allergy Override Reason" (logged for audit).\n\n'
                'توقف! الوصفة تحتوي دواءً يتعارض مع حساسية مسجلة لدى المريض. '
                'احذف الدواء أو وثّق سبب التجاوز.',
                patient=rx.patient_id.name, detail=detail))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_allergy_conflicts()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {'medicine_ids', 'appointment_id', 'allergy_override_reason'} \
                & set(vals):
            self._check_allergy_conflicts()
        return res

    def action_prescribed(self):
        self._check_allergy_conflicts()
        return super().action_prescribed()


class DentalPrescriptionLinesGuard(models.Model):
    _inherit = 'dental.prescription_lines'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.prescription_id._check_allergy_conflicts()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if 'medicament_id' in vals:
            self.prescription_id._check_allergy_conflicts()
        return res

    @api.onchange('medicament_id')
    def _onchange_medicament_allergy(self):
        """Instant warning while editing, before the blocking save check."""
        rx = self.prescription_id
        patient = rx.patient_id
        if not (patient and self.medicament_id):
            return
        label = ' '.join(filter(None, (
            self.medicament_id.name, self.medicament_id.generic_name)))
        conflicts = patient._allergy_conflicts_for([label])
        if conflicts:
            return {'warning': {
                'title': _('⚠ ALLERGY CONFLICT'),
                'message': _(
                    '%(patient)s is allergic to %(sub)s — "%(med)s" matches. '
                    'Saving will be blocked unless an override reason is '
                    'documented.',
                    patient=patient.name, sub=conflicts[0][0], med=label),
            }}
