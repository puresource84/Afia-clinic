# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_medicine = fields.Boolean(string='Is Medicine')
    generic_name = fields.Char(string='Generic Name')
    dosage_strength = fields.Integer(string='Dosage Strength')
