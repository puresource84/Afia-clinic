# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    move_id = fields.Many2one('account.move', string='Related Invoice')
    treatment_name = fields.Char(string='Treatment Done', compute='_compute_from_invoice', store=True)
    treatment_cost = fields.Float(string='Invoice Total', compute='_compute_from_invoice', store=True)
    amount_due = fields.Float(string='Balance Due', compute='_compute_from_invoice', store=True)
    patient_sign = fields.Char(string='Patient Signature')

    @api.depends('move_id', 'move_id.amount_residual', 'move_id.invoice_line_ids')
    def _compute_from_invoice(self):
        # Reads only the payment's own linked invoice — no cross-patient
        # search/aggregation, no N+1.
        for rec in self:
            invoice = rec.move_id
            if invoice:
                first_line = invoice.invoice_line_ids[:1]
                rec.treatment_name = first_line.name if first_line else ''
                rec.treatment_cost = invoice.amount_total
                rec.amount_due = invoice.amount_residual
            else:
                rec.treatment_name = ''
                rec.treatment_cost = 0.0
                rec.amount_due = 0.0
