# -*- coding: utf-8 -*-

from odoo import fields, models


class DentalSpecialist(models.Model):
    """To mention doctors Specialised field"""
    _name = 'dental.specialist'
    _description = "Dental Specialist"

    name = fields.Char(string="Name", help="Name of the dental specialist")
    code = fields.Char(string="Code", help="Add the code for the name")
