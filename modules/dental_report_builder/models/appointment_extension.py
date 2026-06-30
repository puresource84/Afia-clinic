# -*- coding: utf-8 -*-
from odoo import models, fields

class DentalAppointment(models.Model):
    _inherit = 'dental.appointment'

    treatment_id = fields.Many2one('dental.treatment', string="Treatment/Service")
