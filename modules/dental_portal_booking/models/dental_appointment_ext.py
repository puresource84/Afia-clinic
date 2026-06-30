from odoo import models, fields


class DentalAppointmentPortal(models.Model):
    _inherit = 'dental.appointment'

    booking_source = fields.Selection([
        ('manual', 'Manual'),
        ('online', 'Online Portal'),
        ('phone', 'Phone'),
    ], string='Booking Source', default='manual')
    patient_notes = fields.Text(string='Patient Notes')