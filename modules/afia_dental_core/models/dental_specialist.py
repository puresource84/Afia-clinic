# -*- coding: utf-8 -*-
from odoo import fields, models


class DentalSpecialist(models.Model):
    _name = 'dental.specialist'
    _description = 'Dental Specialist'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char()
