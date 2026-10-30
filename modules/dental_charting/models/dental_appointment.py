"""Adds a perio_exam_count stat field + action to dental.appointment."""
from odoo import api, fields, models


class DentalAppointmentPerio(models.Model):
    _inherit = 'dental.appointment'

    perio_exam_ids = fields.One2many(
        'dental.perio.exam', 'appointment_id',
        string='Perio Exams')

    perio_exam_count = fields.Integer(
        string='Perio', compute='_compute_perio_exam_count')

    @api.depends('perio_exam_ids')
    def _compute_perio_exam_count(self):
        for appt in self:
            appt.perio_exam_count = len(appt.perio_exam_ids)

    def action_open_perio_exams(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Perio Exams',
            'res_model': 'dental.perio.exam',
            'view_mode': 'list,form',
            'domain': [('appointment_id', '=', self.id)],
            'context': {
                'default_appointment_id': self.id,
                'default_patient_id': self.patient_id.id,
                'default_dentist_id': self.dentist_id.id
                    if hasattr(self, 'dentist_id') else False,
            },
        }
        if self.perio_exam_count == 1:
            action['view_mode'] = 'form'
            action['res_id'] = self.perio_exam_ids[0].id
        return action
