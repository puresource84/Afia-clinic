# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResPartner(TransactionCase):

    def test_patient_no_only_assigned_to_patients(self):
        non_patient = self.env['res.partner'].create({'name': 'Regular Contact'})
        self.assertFalse(non_patient.patient_no)

        patient = self.env['res.partner'].create({'name': 'A Patient', 'is_patient': True})
        self.assertTrue(patient.patient_no)

    def test_questionnaire_rows_seeded_on_patient_create(self):
        question = self.env['medical.questions'].create({'question': 'Any allergies?'})
        patient = self.env['res.partner'].create({'name': 'Q Patient', 'is_patient': True})
        rows = self.env['medical.questionnaire'].search([('patient_id', '=', patient.id)])
        self.assertIn(question, rows.mapped('question_id'))

    def test_appointment_count_batched(self):
        dentist = self.env['hr.employee'].create({'name': 'Dr. Count', 'is_dentist': True})
        patient = self.env['res.partner'].create({'name': 'Count Patient', 'is_patient': True})
        self.env['dental.appointment'].create({
            'patient_id': patient.id, 'dentist_id': dentist.id,
        })
        self.env['dental.appointment'].create({
            'patient_id': patient.id, 'dentist_id': dentist.id,
        })
        self.assertEqual(patient.appointment_count, 2)

    def test_patient_age_computed_from_dob(self):
        patient = self.env['res.partner'].create({
            'name': 'Age Patient', 'is_patient': True, 'dob': '2000-08-04',
        })
        self.assertGreaterEqual(patient.patient_age, 25)
