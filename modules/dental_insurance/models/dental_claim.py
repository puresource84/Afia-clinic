from odoo import models, fields, api


class DentalClaim(models.Model):
    _name = 'dental.claim'
    _description = 'Insurance Claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Claim No.', readonly=True, copy=False, default='/')
    patient_id = fields.Many2one('res.partner', required=True,
        domain="[('is_patient','=',True)]")
    policy_id = fields.Many2one('dental.policy', required=True)
    insurer_id = fields.Many2one(related='policy_id.insurer_id', store=True)
    appointment_id = fields.Many2one('dental.appointment', string='Appointment')
    treatment_ids = fields.Many2many('dental.treatment', string='Treatments')
    claim_date = fields.Date(default=fields.Date.today)
    total_amount = fields.Float(string='Total Billed')
    approved_amount = fields.Float(string='Approved Amount')
    patient_portion = fields.Float(string='Patient Portion',
        compute='_compute_patient_portion', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pre_auth', 'Pre-Authorised'),
        ('approved', 'Approved'),
        ('partially_approved', 'Partially Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ], default='draft', tracking=True)
    rejection_reason = fields.Text()
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'dental.claim') or '/'
        return super().create(vals_list)

    @api.depends('total_amount', 'approved_amount')
    def _compute_patient_portion(self):
        for r in self:
            r.patient_portion = max(0, r.total_amount - r.approved_amount)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_pre_auth(self):
        self.write({'state': 'pre_auth'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_mark_paid(self):
        self.write({'state': 'paid'})