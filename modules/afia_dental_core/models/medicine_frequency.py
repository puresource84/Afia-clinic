# -*- coding: utf-8 -*-
from odoo import fields, models


class MedicineFrequency(models.Model):
    _name = 'medicine.frequency'
    _description = 'Medicine Frequency'
    _rec_name = 'medicament_frequency'

    code = fields.Char()
    medicament_frequency = fields.Char(string='Frequency', required=True)
