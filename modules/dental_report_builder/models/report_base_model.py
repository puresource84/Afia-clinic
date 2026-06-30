# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DentalReportBaseModel(models.Model):
    _name = 'dental.report.base.model'
    _description = 'Base Model for Reporting'

    name = fields.Char(string="Report Model Name", required=True)
    field_description = fields.Text(string="Description")  # Matches view XML
    model_id = fields.Many2one(
        'ir.model',
        string="Odoo Model",
        ondelete='cascade'  # Required in Odoo 18+
    )
    column_ids = fields.One2many(
        'dental.report.base.model.column',
        'base_model_id',
        string="Model Fields"
    )

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.model_id:
            self.name = self.model_id.name

    @api.constrains('model_id')
    def _check_model_id_required(self):
        for record in self:
            if not record.model_id:
                raise ValidationError("Model selection is required for the report configuration.")

class DentalReportBaseModelColumn(models.Model):
    _name = 'dental.report.base.model.column'
    _description = 'Model Column for Reporting'

    name = fields.Char(string="Field Name", required=True)
    label = fields.Char(string="Label")  # ✅ Matches view
    field_type = fields.Selection([      # ✅ Matches view
        ('char', 'Char'),
        ('text', 'Text'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('datetime', 'Datetime'),
        ('many2one', 'Many2one'),
    ], string="Field Type")
    is_visible = fields.Boolean(string="Visible", default=True)  # ✅ Matches view

    field_description = fields.Char(string="Field Label")  # Optional legacy
    base_model_id = fields.Many2one(
        'dental.report.base.model',
        string="Parent Report Model",
        ondelete='cascade',
        required=True
    )
