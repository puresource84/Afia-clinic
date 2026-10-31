from odoo import models, fields


class DentalInsurer(models.Model):
    _name = 'dental.insurer'
    _description = 'Dental Insurance Company'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', string='Contact')
    phone = fields.Char()
    email = fields.Char()
    website = fields.Char()
    notes = fields.Text()
    policy_ids = fields.One2many('dental.policy', 'insurer_id', string='Policies')
    policy_count = fields.Integer(compute='_compute_policy_count')

    def _compute_policy_count(self):
        for r in self:
            r.policy_count = len(r.policy_ids)