from odoo import models, fields, api


class DentalLabOrder(models.Model):
    _name = 'dental.lab.order'
    _description = 'Dental Lab Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date'

    name = fields.Char(string='Order No.', readonly=True, copy=False, default='/')
    patient_id = fields.Many2one('res.partner', required=True,
        domain="[('is_patient','=',True)]")
    appointment_id = fields.Many2one('dental.appointment')
    dentist_id = fields.Many2one('hr.employee', domain="[('is_dentist','=',True)]")
    lab_name = fields.Char(string='Laboratory Name', required=True)
    lab_contact = fields.Char(string='Lab Contact No.')
    work_type = fields.Selection([
        ('crown', 'Crown'),
        ('bridge', 'Bridge'),
        ('veneer', 'Veneer'),
        ('denture', 'Denture'),
        ('implant', 'Implant Component'),
        ('aligner', 'Aligner / Retainer'),
        ('other', 'Other'),
    ], required=True, default='crown')
    tooth_ids = fields.Many2many('dental.tooth', string='Teeth')
    material = fields.Char(string='Material / Alloy')
    shade = fields.Char(string='Shade')
    order_date = fields.Date(default=fields.Date.today)
    due_date = fields.Date(required=True)
    received_date = fields.Date()
    cost = fields.Float(string='Lab Cost')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent to Lab'),
        ('in_progress', 'In Progress'),
        ('received', 'Received'),
        ('fitted', 'Fitted'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    instructions = fields.Text(string='Lab Instructions')
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'dental.lab.order') or '/'
        return super().create(vals_list)

    def action_send(self):
        self.write({'state': 'sent'})

    def action_receive(self):
        self.write({'state': 'received', 'received_date': fields.Date.today()})

    def action_fit(self):
        self.write({'state': 'fitted'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})