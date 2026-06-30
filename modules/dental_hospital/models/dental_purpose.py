from odoo import models, fields


class DentalPurpose(models.Model):
    _name = 'dental.purpose'
    _description = 'Dental Treatment Purpose'

    name = fields.Char(string='Treatment name', store=True)
