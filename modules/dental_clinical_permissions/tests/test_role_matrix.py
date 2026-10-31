# -*- coding: utf-8 -*-
"""What each clinic role may actually do.

The browser pass on 2026-10-31 walked every role by hand and found six
defects the suite had not caught. The suite did already test roles — lab
orders and insurance both have access-control guards from the 2026-09-20
audit — but only for the models that audit looked at. Prescriptions and
treatment plans were never covered, and they turned out to be the two that
mattered: both still granted write and create to base.group_user, so any
internal user could prescribe. The front end hid the New button and the
boundary looked enforced.

These tests assert the boundary where it is actually enforced.
"""
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestClinicRoleMatrix(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        core = 'afia_dental_core.group_clinic_%s'
        cls.receptionist = new_test_user(
            cls.env, login='afia_role_reception', groups=core % 'receptionist')
        cls.hygienist = new_test_user(
            cls.env, login='afia_role_hygienist', groups=core % 'hygienist')
        cls.dentist = new_test_user(
            cls.env, login='afia_role_dentist', groups=core % 'dentist')
        # The owner-dentist of a small practice: a dentist who also runs the
        # clinic. The ladder covers it, so this is the admin group, which is
        # what the Add Staff User wizard assigns for that option.
        cls.owner_dentist = new_test_user(
            cls.env, login='afia_role_owner', groups=core % 'admin')

        cls.patient = cls.env['res.partner'].create(
            {'name': 'Role Matrix Patient', 'is_patient': True})
        cls.employee = cls.env['hr.employee'].create(
            {'name': 'Dr Role Matrix', 'is_dentist': True})
        cls.appointment = cls.env['dental.appointment'].create({
            'patient_id': cls.patient.id,
            'dentist_id': cls.employee.id,
        })

    def _rx_vals(self):
        return {
            'appointment_id': self.appointment.id,
            'patient_id': self.patient.id,
            'prescribed_doctor_id': self.employee.id,
        }

    # ── the ladder itself ────────────────────────────────────────────────
    # Every capability below is inherited rather than granted twice, so if
    # the chain breaks the rest of this file stops meaning anything.

    def test_role_ladder_is_intact(self):
        ref = self.env.ref
        admin = ref('afia_dental_core.group_clinic_admin')
        dentist = ref('afia_dental_core.group_clinic_dentist')
        hygienist = ref('afia_dental_core.group_clinic_hygienist')
        reception = ref('afia_dental_core.group_clinic_receptionist')
        self.assertIn(dentist, admin.implied_ids,
                      'Clinic Administrator must imply Dentist')
        self.assertIn(hygienist, dentist.implied_ids,
                      'Dentist must imply Hygienist')
        self.assertIn(reception, hygienist.implied_ids,
                      'Hygienist must imply Receptionist')

    def test_owner_dentist_inherits_every_clinical_group(self):
        groups = self.owner_dentist.groups_id
        for name in ('dentist', 'hygienist', 'receptionist'):
            self.assertIn(
                self.env.ref('afia_dental_core.group_clinic_%s' % name), groups,
                'the admin rung must carry %s with it' % name)

    # ── prescribing ──────────────────────────────────────────────────────

    def test_receptionist_cannot_prescribe(self):
        with self.assertRaises(AccessError):
            self.env['dental.prescription'].with_user(
                self.receptionist).create(self._rx_vals())

    def test_hygienist_cannot_prescribe(self):
        with self.assertRaises(AccessError):
            self.env['dental.prescription'].with_user(
                self.hygienist).create(self._rx_vals())

    def test_dentist_can_prescribe(self):
        rx = self.env['dental.prescription'].with_user(
            self.dentist).create(self._rx_vals())
        self.assertTrue(rx.sequence_no, 'the sequence must be allocated')

    def test_owner_dentist_can_prescribe(self):
        rx = self.env['dental.prescription'].with_user(
            self.owner_dentist).create(self._rx_vals())
        self.assertTrue(rx.sequence_no)

    def test_receptionist_may_still_read_prescriptions(self):
        """Reading is deliberate: the front desk collects payment for them."""
        rx = self.env['dental.prescription'].create(self._rx_vals())
        self.assertTrue(rx.with_user(self.receptionist).sequence_no)

    # ── treatment plans ──────────────────────────────────────────────────

    def test_hygienist_cannot_create_treatment_plan(self):
        with self.assertRaises(AccessError):
            self.env['dental.treatment.plan'].with_user(
                self.hygienist).create({'patient_id': self.patient.id})

    def test_dentist_can_create_treatment_plan(self):
        plan = self.env['dental.treatment.plan'].with_user(
            self.dentist).create({'patient_id': self.patient.id})
        self.assertEqual(plan.patient_id, self.patient)

    # ── periodontal charting ─────────────────────────────────────────────

    def test_hygienist_can_create_perio_exam(self):
        """Charting is hygienist work. The ACLs always allowed this; until
        2026-10-31 the menu was scoped to dentist and above, so the role
        that does the charting could not reach the screen."""
        exam = self.env['dental.perio.exam'].with_user(
            self.hygienist).create({'patient_id': self.patient.id})
        self.assertEqual(len(exam.reading_ids), 28)

    def test_receptionist_cannot_create_perio_exam(self):
        with self.assertRaises(AccessError):
            self.env['dental.perio.exam'].with_user(
                self.receptionist).create({'patient_id': self.patient.id})
