from odoo import models
from odoo.exceptions import UserError


class DentalConsentFormSignature(models.Model):
    """B3: enforce a real e-signature before a consent form can be signed."""
    _inherit = 'dental.consent.form'

    def action_sign(self):
        for rec in self:
            if rec.template_id.requires_signature and not rec.patient_signature:
                raise UserError(
                    'This consent template requires a patient signature. '
                    'Use the signature pad on the form.')
            if not rec.signed_by:
                raise UserError(
                    'Enter the printed name of the signer '
                    '(Signed By) before marking signed.')
        return super().action_sign()
