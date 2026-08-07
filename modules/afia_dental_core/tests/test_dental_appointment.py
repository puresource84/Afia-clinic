# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDentalAppointment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.patient = cls.env['res.partner'].create({
            'name': 'Test Patient',
            'is_patient': True,
        })
        cls.dentist_employee = cls.env['hr.employee'].create({
            'name': 'Dr. Test Dentist',
            'is_dentist': True,
        })

    def _create_appointment(self, **extra):
        vals = {
            'patient_id': self.patient.id,
            'dentist_id': self.dentist_employee.id,
        }
        vals.update(extra)
        return self.env['dental.appointment'].create(vals)

    def test_sequence_assigned_on_create(self):
        appt = self._create_appointment()
        self.assertNotEqual(appt.appointment_no, 'New')
        self.assertTrue(appt.appointment_no)

    def test_patient_no_backfilled_on_create(self):
        # res.partner.create() already backfills patient_no the moment a
        # patient record is created (see models/res_partner.py) — this
        # test guards the appointment-side safety net (_ensure_patient_no)
        # for patients that predate that behavior, e.g. records created
        # directly via SQL/import with is_patient=True but no patient_no.
        self.assertTrue(self.patient.patient_no)
        patient_no = self.patient.patient_no

        legacy_patient = self.patient.sudo().with_context(tracking_disable=True)
        self.env.cr.execute(
            "UPDATE res_partner SET patient_no = NULL WHERE id = %s", (legacy_patient.id,))
        self.patient.invalidate_recordset(['patient_no'])
        self.assertFalse(self.patient.patient_no)

        self._create_appointment()
        self.assertTrue(self.patient.patient_no)

        # restore for other tests sharing the class-level patient
        self.patient.patient_no = patient_no

    def test_appointment_date_computed_from_start_datetime(self):
        appt = self._create_appointment()
        self.assertEqual(appt.appointment_date, appt.start_datetime.date())

    def test_stop_datetime_follows_duration(self):
        appt = self._create_appointment(duration=1.0)
        delta = appt.stop_datetime - appt.start_datetime
        self.assertAlmostEqual(delta.total_seconds() / 3600.0, 1.0, places=2)

    def test_calendar_event_created_and_synced(self):
        appt = self._create_appointment()
        self.assertTrue(appt.calendar_event_id)
        self.assertEqual(appt.calendar_event_id.start, appt.start_datetime)

        appt.write({'duration': 2.0})
        self.assertAlmostEqual(
            (appt.calendar_event_id.stop - appt.calendar_event_id.start).total_seconds() / 3600.0,
            2.0, places=2)

    def test_state_machine_start_requires_confirmed(self):
        appt = self._create_appointment()
        with self.assertRaises(UserError):
            appt.action_start()

        appt.action_confirm()
        self.assertEqual(appt.state, 'confirmed')
        appt.action_start()
        self.assertEqual(appt.state, 'in_progress')
        appt.action_done()
        self.assertEqual(appt.state, 'done')

    def test_cancel_deactivates_calendar_event(self):
        appt = self._create_appointment()
        appt.action_cancel()
        self.assertEqual(appt.state, 'cancelled')
        self.assertFalse(appt.calendar_event_id.active)

    def test_unlink_removes_linked_calendar_event(self):
        appt = self._create_appointment()
        event = appt.calendar_event_id
        appt.unlink()
        self.assertFalse(event.exists())

    def test_duration_must_be_positive(self):
        with self.assertRaises(Exception):
            self._create_appointment(duration=0)
            self.env.flush_all()
