from odoo import models, fields

class DentalTooth(models.Model):
    _name = 'dental.tooth'
    _description = 'Dental Tooth'

    name = fields.Char(string="Tooth Number", required=True)
    condition = fields.Selection([
        ('healthy', 'Healthy'),
        ('cavity', 'Cavity'),
        ('missing', 'Missing'),
        ('filled', 'Filled'),
    ], string="Condition", default="healthy")