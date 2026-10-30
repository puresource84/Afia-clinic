from odoo import models, fields


class ResCompanyBranch(models.Model):
    _inherit = 'res.company'

    is_branch = fields.Boolean(string='Is Branch Clinic', default=False)
    parent_clinic_id = fields.Many2one(
        'res.company', string='Parent Clinic',
        domain="[('is_branch','=',False),('id','!=',id)]")
    branch_ids = fields.One2many(
        'res.company', 'parent_clinic_id', string='Branch Clinics')
    branch_code = fields.Char(string='Branch Code')
    branch_count = fields.Integer(compute='_compute_branch_count')

    def _compute_branch_count(self):
        for r in self:
            r.branch_count = len(r.branch_ids)