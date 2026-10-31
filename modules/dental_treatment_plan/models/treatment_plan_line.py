from odoo import models, fields


class DentalTreatmentPlanLine(models.Model):
    _name = 'dental.treatment.plan.line'
    _description = 'Treatment Plan Session'
    _order = 'sequence, id'

    plan_id = fields.Many2one('dental.treatment.plan', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Session Description', required=True)
    treatment_ids = fields.Many2many('dental.treatment', string='Treatments')
    appointment_id = fields.Many2one('dental.appointment', string='Appointment')
    scheduled_date = fields.Date(string='Scheduled Date')
    cost = fields.Float(string='Estimated Cost')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('done', 'Done'),
        ('skipped', 'Skipped'),
    ], default='pending')
    notes = fields.Text()