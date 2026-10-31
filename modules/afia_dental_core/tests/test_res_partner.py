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
        # Different times: the same dentist can't be double-booked.
        self.env['dental.appointment'].create({
            'patient_id': patient.id, 'dentist_id': dentist.id,
            'start_datetime': '2030-01-01 08:00:00',
        })
        self.env['dental.appointment'].create({
            'patient_id': patient.id, 'dentist_id': dentist.id,
            'start_datetime': '2030-01-01 09:00:00',
        })
        self.assertEqual(patient.appointment_count, 2)

    def test_patient_age_computed_from_dob(self):
        patient = self.env['res.partner'].create({
            'name': 'Age Patient', 'is_patient': True, 'dob': '2000-08-04',
        })
        self.assertGreaterEqual(patient.patient_age, 25)

    def test_appointment_count_uses_batched_afia_dental_core_compute(self):
        """Regression guard for
        afia_dental_core-duplicate-appointment-button: dental_ux_fixes
        used to redefine appointment_count with a per-record
        search_count() loop that shadowed this module's batched
        _read_group() implementation (dental_ux_fixes loads after
        afia_dental_core, so its copy silently won). Assert the compute
        method Odoo actually registered is this module's, not a
        redefinition elsewhere, so an N+1 regression can't silently
        creep back in via another module doing the same thing."""
        compute_method = type(self.env['res.partner'])._compute_appointment_count
        self.assertIn(
            'afia_dental_core', compute_method.__module__,
            'appointment_count compute must resolve to afia_dental_core\'s '
            'batched implementation, not a per-record override from '
            'another module.')

    def test_action_view_appointments_single_definition(self):
        """Regression guard: action_view_appointments must not be
        redefined in dental_ux_fixes (or elsewhere) shadowing this
        module's copy — see afia_dental_core-duplicate-appointment-button."""
        action_method = type(self.env['res.partner']).action_view_appointments
        self.assertIn('afia_dental_core', action_method.__module__)
