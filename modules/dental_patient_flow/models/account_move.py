from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _invoice_paid_hook(self):
        """Move the visit card to Paid on the front-desk board as soon as its
        invoice is paid, whichever way the payment was registered."""
        res = super()._invoice_paid_hook()
        invoices = self.filtered('is_treatment_invoice')
        if invoices:
            self.env['dental.appointment'].sudo().search([
                ('invoice_ids', 'in', invoices.ids),
            ])._sync_flow_paid_from_invoices()
        return res
