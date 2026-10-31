# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_treatment_invoice = fields.Boolean(string='Treatment Invoice', default=False)

    # 2026-08-21, per Manhel: a treatment invoice created for a partner did
    # not automatically flag that partner as a patient (res.partner.is_patient
    # stays False unless the partner was created through the Patients app's
    # own "New" button, which is the only place that ever set it). Views like
    # Invoices/Payments/Reporting filter on partner_id.is_patient = True, so a
    # perfectly valid, posted, paid invoice could be silently invisible there
    # if its customer wasn't separately created as a "Patient" first — this
    # is exactly what happened with INV/2026/00057 (partner "بتول الحلبي").
    # Self-healing fix: whenever a move is a treatment invoice, make sure its
    # partner is flagged. Covers both new invoices (create) and the case
    # where is_treatment_invoice or partner_id is set/changed afterwards
    # (write). See afia_dental_core/migrations/18.0.2.0.5 for the one-time
    # backfill of already-existing affected invoices.
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.filtered('is_treatment_invoice')._sync_patient_flag()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'is_treatment_invoice' in vals or 'partner_id' in vals:
            self.filtered('is_treatment_invoice')._sync_patient_flag()
        return res

    def _sync_patient_flag(self):
        partners = self.mapped('partner_id').filtered(lambda p: not p.is_patient)
        if partners:
            partners.write({'is_patient': True})
