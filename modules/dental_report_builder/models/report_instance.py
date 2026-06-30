# -*- coding: utf-8 -*-
from odoo import models, fields
import json

class ReportInstance(models.Model):
    _name = 'dental.report.instance'
    _description = 'Report Instance'

    name = fields.Char(string="Report Name")
    advanced_model_id = fields.Many2one('dental.report.advanced.model', string="Report Definition")
    result_data = fields.Text(string="Result JSON")
    generated_at = fields.Datetime(string="Generated At", default=fields.Datetime.now)

    def action_generate_report(self):
        if self.advanced_model_id.technical_name == 'upcoming_appointments':
            self.result_data = json.dumps(self._fetch_upcoming_appointments())
        elif self.advanced_model_id.technical_name == 'patients_by_treatment':
            self.result_data = json.dumps(self._fetch_patients_by_treatment())
        else:
            self.result_data = json.dumps([])

    def _fetch_upcoming_appointments(self):
        appointments = self.env['dental.appointment'].search([
            ('appointment_date', '>=', fields.Date.today())
        ], limit=100)

        return [{
            'patient_name': appt.patient_id.name if appt.patient_id else '',
            'dentist_name': appt.dentist_id.name if hasattr(appt, 'dentist_id') and appt.dentist_id else '',
            'treatment_name': appt.treatment_id.name if appt.treatment_id else '',
            'date': appt.appointment_date.strftime('%Y-%m-%d') if appt.appointment_date else '',
            'status': appt.status or ''
        } for appt in appointments]

    def _fetch_patients_by_treatment(self):
        treatments = self.env['dental.treatment'].search([], limit=100)

        return [{
            'patient_name': treatment.patient_id.name if treatment.patient_id else '',
            'treatment_name': treatment.name,
            'start_date': treatment.start_date.strftime('%Y-%m-%d') if treatment.start_date else '',
            'end_date': treatment.end_date.strftime('%Y-%m-%d') if treatment.end_date else '',
            'dentist_name': treatment.dentist_id.name if treatment.dentist_id else '',
        } for treatment in treatments]
