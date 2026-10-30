from odoo import api, fields, models


class ResPartnerAllergy(models.Model):
    _inherit = 'res.partner'

    allergy_alert = fields.Text(
        string='Allergies / Clinical Alerts', tracking=True,
        help='Shown as a red alert on the patient and every appointment. '
             'E.g. "PENICILLIN allergy", "anticoagulant therapy", "diabetic".')

    # ── Clinical / Medical notes (replaces unused vendor fields in Internal Notes) ──

    clinical_notes = fields.Text(
        string='Clinical Notes',
        help='Free-text clinical observations, ongoing conditions, treatment notes.',
    )
    insurance_notes = fields.Text(
        string='Insurance / Coverage Notes',
        help='Insurance provider, policy number, coverage limits, pre-auth notes.',
    )
    consent_signed = fields.Boolean(
        string='Consent Form Signed',
        default=False,
        help='Patient has signed the clinic consent form.',
    )
    consent_date = fields.Date(
        string='Consent Date',
        help='Date the patient signed the consent form.',
    )


class DentalAppointmentAllergy(models.Model):
    _inherit = 'dental.appointment'

    allergy_alert = fields.Text(
        related='patient_id.allergy_alert', string='Clinical Alerts',
        readonly=True)

    @api.onchange('patient_id')
    def _onchange_patient_allergy_warning(self):
        """NOW-bucket A4: hard visual stop when selecting an at-risk patient."""
        if self.patient_id and self.patient_id.allergy_alert:
            return {'warning': {
                'title': '⚠ CLINICAL ALERT',
                'message': '%s:\n%s' % (self.patient_id.name,
                                        self.patient_id.allergy_alert),
            }}
