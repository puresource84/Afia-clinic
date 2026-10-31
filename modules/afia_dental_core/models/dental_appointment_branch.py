from odoo import models, fields


class DentalAppointmentBranch(models.Model):
    _inherit = 'dental.appointment'

    branch_id = fields.Many2one(
        'res.company', string='Branch / Location',
        default=lambda self: self.env.company)