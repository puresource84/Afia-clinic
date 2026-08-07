# -*- coding: utf-8 -*-
from odoo import fields, models


class TreatmentCategory(models.Model):
    _name = 'treatment.category'
    _description = 'Treatment Category'

    name = fields.Char(required=True)
    treatment_ids = fields.One2many('dental.treatment', 'treatment_categ_id', string='Treatments')


class DentalTreatment(models.Model):
    _name = 'dental.treatment'
    _description = 'Dental Treatment'
    _order = 'name'

    name = fields.Char(string='Treatment Name', required=True)
    treatment_categ_id = fields.Many2one('treatment.category', string='Category')
    cost = fields.Float(string='Cost')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id)
    active = fields.Boolean(default=True)
