# -*- coding: utf-8 -*-
from odoo import fields, models


class DentalTooth(models.Model):
    _name = 'dental.tooth'
    _description = 'Dental Tooth'
    _order = 'name'

    name = fields.Char(string='Tooth Number', required=True)
    condition = fields.Selection([
        ('healthy', 'Healthy'),
        ('cavity', 'Cavity'),
        ('missing', 'Missing'),
        ('filled', 'Filled'),
    ], default='healthy')
