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
    # NOTE (2026-08-16): do NOT add a default_duration field here.
    # dental_appointment_times already extends this model with
    # default_duration (its onchange feeds apt_duration/apt_end_time, wired
    # into shift + double-booking checks). A duplicate declaration here
    # briefly existed and silently merged into the same column (harmless)
    # but shadowed that module's onchange and duplicated the list-view
    # column. See project_afia_click_everywhere_qa_2026-08-15 memory.
