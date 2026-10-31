# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAvailability(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.partner_id.tz = 'Asia/Baghdad'
        cls.Apt = cls.env['dental.appointment']
        cls.shift = cls.env['dental.time.shift'].create(
            {'start_time': 9.0, 'end_time': 11.0})
        cls.dentist = cls.env['hr.employee'].create({
            'name': 'Dr. Slots', 'is_dentist': True,
            'time_shift_ids': [(6, 0, cls.shift.ids)]})
        cls.patient = cls.env['res.partner'].create(
            {'name': 'Slot Patient', 'is_patient': True})
        cls.day = date.today() + timedelta(days=7)

    def _book(self, hour, duration=0.5, **kw):
        return self.Apt.create(dict({
            'patient_id': self.patient.id,
            'dentist_id': self.dentist.id,
            'start_datetime': self.Apt._local_to_utc(self.day, hour),
            'duration': duration,
        }, **kw))

    def test_slots_follow_shift(self):
        self.assertEqual(self.Apt.get_available_slots(self.dentist.id, self.day),
                         [9.0, 9.5, 10.0, 10.5])

    def test_staff_booking_hides_slot(self):
        """Appointments booked by staff (no website slot) block the slot too."""
        self._book(9.5, duration=1.0)  # 09:30-10:30
        self.assertEqual(self.Apt.get_available_slots(self.dentist.id, self.day),
                         [9.0, 10.5])

    def test_double_booking_blocked(self):
        self._book(10.0)
        with self.assertRaises(ValidationError):
            self._book(10.0)
        with self.assertRaises(ValidationError):
            self._book(9.75)  # partial overlap

    def test_back_to_back_allowed(self):
        self._book(9.0)
        self._book(9.5)

    def test_urgent_squeeze_in_allowed(self):
        self._book(10.0)
        self._book(10.0, urgency='urgent')

    def test_cancelled_frees_slot(self):
        apt = self._book(10.0)
        apt.action_cancel()
        self._book(10.0)

    def test_moving_into_busy_time_blocked(self):
        self._book(9.0)
        other = self._book(10.0)
        with self.assertRaises(ValidationError):
            other.start_datetime = self.Apt._local_to_utc(self.day, 9.0)

    def test_public_holiday_blocks_day(self):
        self.env['resource.calendar.leaves'].create({
            'name': 'Holiday',
            'date_from': self.Apt._local_to_utc(self.day, 0),
            'date_to': self.Apt._local_to_utc(self.day, 24),
            'calendar_id': self.dentist.resource_calendar_id.id,
        })
        self.assertEqual(
            self.Apt.get_available_slots(self.dentist.id, self.day), [])

    def test_past_slots_excluded(self):
        yesterday = date.today() - timedelta(days=1)
        self.assertEqual(
            self.Apt.get_available_slots(self.dentist.id, yesterday), [])
