# -*- coding: utf-8 -*-
from odoo import fields, models


class DentalPurpose(models.Model):
    _name = 'dental.purpose'
    _description = 'Dental Treatment Purpose'

    name = fields.Char(string='Purpose', required=True)
