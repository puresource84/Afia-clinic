# -*- coding: utf-8 -*-

from odoo import fields, models


class DentalTreatment(models.Model):
    """For adding Dental treatment details of the patients"""
    _name = 'dental.treatment'
    _description = "Dental Treatment"

    name = fields.Char(string='Treatment Name', help="Date of the treatment")
    treatment_categ_id = fields.Many2one('treatment.category',
                                         string="Category",
                                         help="name of the treatment")
    cost = fields.Float(string='Cost',
                        help="Cost of the Treatment")
