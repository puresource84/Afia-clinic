from odoo import models, fields, api
from datetime import timedelta


class SterilizationLog(models.Model):
    _name = 'dental.sterilization.log'
    _description = 'Instrument Sterilization Cycle Log'
    _inherit = ['mail.thread']
    _order = 'cycle_date desc'

    name = fields.Char(string='Cycle Ref', readonly=True, copy=False, default='/')
    cycle_date = fields.Datetime(default=fields.Datetime.now, required=True)
    operator_id = fields.Many2one('res.users', default=lambda s: s.env.user)
    instrument_set = fields.Char(string='Instrument Set / Cassette', required=True)
    autoclave_id = fields.Char(string='Autoclave Unit ID')
    cycle_type = fields.Selection([
        ('class_b', 'Class B (Vacuum)'),
        ('class_s', 'Class S (Simple)'),
        ('class_n', 'Class N (Gravity)'),
        ('chemical', 'Chemical Disinfection'),
    ], string='Cycle Type', required=True, default='class_b')
    temperature = fields.Float(string='Temperature (°C)')
    pressure = fields.Float(string='Pressure (bar)')
    duration_min = fields.Integer(string='Duration (min)')
    load_number = fields.Char(string='Load / Batch Number')
    biological_indicator = fields.Selection([
        ('not_used', 'Not Used'),
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], default='not_used')
    expiry_date = fields.Date(
        string='Pack Expiry Date',
        compute='_compute_expiry', store=True)
    state = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('pending', 'Pending Validation'),
    ], default='pending', tracking=True)
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'dental.sterilization.log') or '/'
        return super().create(vals_list)

    @api.depends('cycle_date')
    def _compute_expiry(self):
        for r in self:
            if r.cycle_date:
                r.expiry_date = r.cycle_date.date() + timedelta(days=180)
            else:
                r.expiry_date = False

    def action_pass(self):
        self.write({'state': 'pass'})

    def action_fail(self):
        self.write({'state': 'fail'})