# -*- coding: utf-8 -*-
"""Patient extension of res.partner. Clean-room rewrite (2026-08)."""
from datetime import date

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_patient = fields.Boolean(string='Is a Patient', default=False, index=True)
    patient_no = fields.Char(string='Patient No.', copy=False, index=True)
    company_type = fields.Selection(selection_add=[
        ('person', 'Patient'),
        ('company', 'Medicine Distributor'),
    ])

    dob = fields.Date(string='Date of Birth')
    patient_age = fields.Integer(
        string='Age', compute='_compute_patient_age', store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')

    medical_questionnaire_ids = fields.One2many(
        'medical.questionnaire', 'patient_id', string='Medical Questionnaire')
    appointment_ids = fields.One2many(
        'dental.appointment', 'patient_id', string='Appointments')
    appointment_count = fields.Integer(compute='_compute_appointment_count')
    report_ids = fields.One2many(
        'xray.report', 'patient_id', string='X-Ray Reports')

    @api.depends('dob')
    def _compute_patient_age(self):
        today = date.today()
        for partner in self:
            if partner.dob:
                dob = partner.dob
                partner.patient_age = today.year - dob.year - (
                    (today.month, today.day) < (dob.month, dob.day))
            else:
                partner.patient_age = 0

    def _compute_appointment_count(self):
        # One read_group for the whole recordset instead of a search_count
        # per record.
        groups = self.env['dental.appointment']._read_group(
            [('patient_id', 'in', self.ids)], ['patient_id'], ['__count'])
        counts = {partner.id: count for partner, count in groups}
        for partner in self:
            partner.appointment_count = counts.get(partner.id, 0)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])
        if name:
            args = ['|', ('name', operator, name), ('patient_no', operator, name)] + args
            return self._search(args, limit=limit)
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        new_patients = records.filtered('is_patient')
        for record in new_patients:
            if not record.patient_no:
                record.patient_no = self.env['ir.sequence'].next_by_code(
                    'dental.patient') or _('New')
        if new_patients:
            questions = self.env['medical.questions'].search([('active', '=', True)])
            self.env['medical.questionnaire'].create([
                {'patient_id': p.id, 'question_id': q.id}
                for p in new_patients for q in questions
            ])
        return records

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Appointments'),
            'res_model': 'dental.appointment',
            'view_mode': 'list,form,calendar',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_prescription(self):
        self.ensure_one()
        Prescription = self.env['dental.prescription']
        prescriptions = Prescription.search([('patient_id', '=', self.id)])
        latest_appointment = self.env['dental.appointment'].search(
            [('patient_id', '=', self.id)], order='start_datetime desc', limit=1)

        if prescriptions:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Prescriptions'),
                'view_mode': 'list,form',
                'res_model': 'dental.prescription',
                'domain': [('id', 'in', prescriptions.ids)],
                'context': {'default_patient_id': self.id},
            }
        prescription = Prescription.create({
            'appointment_id': latest_appointment.id if latest_appointment else False,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Prescription'),
            'view_mode': 'form',
            'res_model': 'dental.prescription',
            'res_id': prescription.id,
        }

    def action_open_patient_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Patient Payments'),
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'search_default_partner_id': self.id},
        }
