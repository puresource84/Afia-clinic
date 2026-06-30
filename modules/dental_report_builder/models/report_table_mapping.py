# -*- coding: utf-8 -*-
from odoo import models, fields

class ReportTableMapping(models.Model):
    _name = 'dental.report.table.mapping'
    _description = 'Report Table Mapping'

    name = fields.Char(required=True)
    base_model_ids = fields.Many2many('dental.report.base.model', string="Mapped Base Models")
