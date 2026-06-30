# -*- coding: utf-8 -*-
from odoo import models, fields

class DentalTreatment(models.Model):
    _inherit = 'dental.treatment'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    patient_id = fields.Many2one(
        'res.partner',
        string="Patient",
        domain="[('is_patient','=',True)]"
    )
    dentist_id = fields.Many2one(
        'res.partner',
        string="Dentist",
        domain="[('is_dentist','=',True)]"
    )
