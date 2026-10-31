from odoo import models, fields, api


class DentalTreatmentPlan(models.Model):
    _name = 'dental.treatment.plan'
    _description = 'Dental Treatment Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Plan Ref', readonly=True, copy=False, default='/')
    patient_id = fields.Many2one('res.partner', string='Patient', required=True,
        domain="[('is_patient','=',True)]")
    dentist_id = fields.Many2one('hr.employee', string='Dentist',
        domain="[('is_dentist','=',True)]")
    diagnosis = fields.Text(string='Diagnosis / Chief Complaint')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    line_ids = fields.One2many('dental.treatment.plan.line', 'plan_id', string='Sessions')
    total_sessions = fields.Integer(compute='_compute_session_stats', store=True)
    completed_sessions = fields.Integer(compute='_compute_session_stats', store=True)
    progress_pct = fields.Float(string='Progress %', compute='_compute_session_stats', store=True)
    total_cost = fields.Float(compute='_compute_total_cost', store=True)
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'dental.treatment.plan') or '/'
        return super().create(vals_list)

    @api.depends('line_ids.state')
    def _compute_session_stats(self):
        for r in self:
            total = len(r.line_ids)
            done = len(r.line_ids.filtered(lambda l: l.state == 'done'))
            r.total_sessions = total
            r.completed_sessions = done
            r.progress_pct = (done / total * 100) if total else 0

    @api.depends('line_ids.cost')
    def _compute_total_cost(self):
        for r in self:
            r.total_cost = sum(r.line_ids.mapped('cost'))

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})