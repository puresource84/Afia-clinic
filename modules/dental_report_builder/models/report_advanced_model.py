# -*- coding: utf-8 -*-
from odoo import models, fields

class ReportAdvancedModel(models.Model):
    _name = 'dental.report.advanced.model'
    _description = 'Report Advanced Model'

    name = fields.Char(required=True)
    base_model_id = fields.Many2one('dental.report.base.model', required=True)
    filter_ids = fields.One2many('dental.report.advanced.filter', 'advanced_model_id', string="Filters")

class ReportAdvancedFilter(models.Model):
    _name = 'dental.report.advanced.filter'
    _description = 'Advanced Filter'

    advanced_model_id = fields.Many2one('dental.report.advanced.model', required=True, ondelete='cascade')
    field_name = fields.Char(required=True)
    operator = fields.Selection([
        ('=', '='), ('!=', '!='), ('>', '>'), ('<', '<'), ('ilike', 'Contains')
    ], required=True)
    value = fields.Char(required=True)
