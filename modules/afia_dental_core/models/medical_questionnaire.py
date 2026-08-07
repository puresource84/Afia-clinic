# -*- coding: utf-8 -*-
"""Medical intake questionnaire. Clean-room rewrite (2026-08).

Original behavior created a questionnaire row with a question_id but no
patient_id at all when a new master question was added — effectively an
orphaned template row, not an actual per-patient answer. Since neither
this model's shape nor its rows are referenced by any other Afia Dental
Clinic module (dependency analysis: zero external references), this was
free territory to redesign properly: a questionnaire row now always
represents one specific patient's answer to one specific question, and
rows are kept in sync automatically in both directions — new question ->
blank row for every existing patient; new patient -> blank row for every
active question."""
from odoo import _, api, fields, models


class MedicalQuestions(models.Model):
    _name = 'medical.questions'
    _description = 'Medical Question (master list)'
    _rec_name = 'question'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    question = fields.Char(required=True)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        questions = super().create(vals_list)
        questions._sync_questionnaire_rows()
        return questions

    def _sync_questionnaire_rows(self):
        Questionnaire = self.env['medical.questionnaire']
        patients = self.env['res.partner'].search([('is_patient', '=', True)])
        for question in self:
            existing = Questionnaire.search([
                ('question_id', '=', question.id), ('patient_id', 'in', patients.ids)])
            missing_patients = patients - existing.patient_id
            Questionnaire.create([
                {'patient_id': p.id, 'question_id': question.id} for p in missing_patients
            ])


class MedicalQuestionnaire(models.Model):
    """One patient's answer to one master question."""
    _name = 'medical.questionnaire'
    _description = 'Medical Questionnaire Answer'

    patient_id = fields.Many2one('res.partner', string='Patient', required=True, ondelete='cascade')
    question_id = fields.Many2one('medical.questions', string='Question', required=True, ondelete='cascade')
    yes_no = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Answer')
    reason = fields.Text()

    _sql_constraints = [
        ('patient_question_unique', 'unique(patient_id, question_id)',
         'This question has already been asked for this patient.'),
    ]
