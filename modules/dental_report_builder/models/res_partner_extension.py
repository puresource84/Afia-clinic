# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_patient = fields.Boolean(string="Is a Patient", default=False)
    is_dentist = fields.Boolean(string="Is a Dentist", default=False)
