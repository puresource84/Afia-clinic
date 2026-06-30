"""
dental.treatment.category — taxonomy for grouping SOAP templates and procedures.

Used by:
  - dental.soap.template.category_id  (link templates to a procedure type)
"""
from odoo import fields, models


class DentalTreatmentCategory(models.Model):
    _name = 'dental.treatment.category'
    _description = 'Treatment Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Color Index', default=0)
    note = fields.Text(string='Notes')

    # Reverse relation: templates in this category
    template_ids = fields.One2many(
        'dental.soap.template', 'category_id',
        string='SOAP Templates')
    template_count = fields.Integer(
        compute='_compute_template_count', string='Templates')

    def _compute_template_count(self):
        for cat in self:
            cat.template_count = len(cat.template_ids)
