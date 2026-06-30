from odoo import models, fields


class DentalPolicy(models.Model):
    _name = 'dental.policy'
    _description = 'Patient Insurance Policy'
    _inherit = ['mail.thread']

    name = fields.Char(string='Policy Number', required=True)
    patient_id = fields.Many2one('res.partner', required=True,
        domain="[('is_patient','=',True)]")
    insurer_id = fields.Many2one('dental.insurer', required=True)
    member_id = fields.Char(string='Member ID')
    group_number = fields.Char(string='Group Number')
    start_date = fields.Date(string='Valid From')
    end_date = fields.Date(string='Valid To')
    coverage_pct = fields.Float(string='Coverage %', default=80.0)
    annual_max = fields.Float(string='Annual Maximum')
    state = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], default='active', tracking=True)
    notes = fields.Text()
    claim_ids = fields.One2many('dental.claim', 'policy_id', string='Claims')
    claim_count = fields.Integer(compute='_compute_claim_count')

    def _compute_claim_count(self):
        for r in self:
            r.claim_count = len(r.claim_ids)