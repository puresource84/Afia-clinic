from odoo import _, models
from odoo.exceptions import UserError


class DentalPrescription(models.Model):
    _inherit = 'dental.prescription'

    def action_create_invoice(self):
        """Bill the prescription as part of its visit's single invoice
        instead of creating separate treatment/medicine invoices, so a
        treatment can't be billed once from the prescription and again
        from the appointment."""
        self.ensure_one()
        if not self.treatment_id:
            raise UserError(_('Select a treatment before invoicing.'))
        apt = self.appointment_id
        invoice = apt._get_active_invoices()[:1]
        if not invoice:
            if apt.state != 'done':
                raise UserError(_(
                    'Mark the prescription as Prescribed (this completes '
                    'the visit) before invoicing.'))
            invoice = apt._create_visit_invoice()
        return apt._action_open_invoice(invoice)
