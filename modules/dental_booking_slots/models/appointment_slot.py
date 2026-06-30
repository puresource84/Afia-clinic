from datetime import datetime, timedelta, timezone

from odoo import api, fields, models
from odoo.exceptions import ValidationError

SLOT_HOURS = 0.5  # 30-minute slots
BAGHDAD_UTC_OFFSET = 3  # clinic timezone (E2 full fix pending)


def _fmt(value):
    """8.5 -> '08:30'"""
    hours = int(value)
    minutes = int(round((value - hours) * 60))
    return '%02d:%02d' % (hours, minutes)


class DentalAppointmentSlot(models.Model):
    _inherit = 'dental.appointment'

    booking_slot = fields.Float(
        string='Time Slot', default=0.0, copy=False,
        help='Start time of the booked 30-min slot (in hours). '
             '0 = whole-shift booking (manual/legacy).')
    booking_slot_display = fields.Char(
        string='Slot', compute='_compute_booking_slot_display')

    @api.depends('booking_slot')
    def _compute_booking_slot_display(self):
        for apt in self:
            apt.booking_slot_display = (
                _fmt(apt.booking_slot) if apt.booking_slot else '')

    @api.constrains('dentist_id', 'appointment_date', 'booking_slot', 'state')
    def _check_slot_double_booking(self):
        for apt in self:
            if not apt.booking_slot or apt.state == 'cancelled':
                continue
            dup = self.search_count([
                ('id', '!=', apt.id),
                ('dentist_id', '=', apt.dentist_id.id),
                ('appointment_date', '=', apt.appointment_date),
                ('booking_slot', '=', apt.booking_slot),
                ('state', '!=', 'cancelled'),
            ])
            if dup:
                raise ValidationError(
                    'Slot %s on %s is already booked for %s.' % (
                        _fmt(apt.booking_slot), apt.appointment_date,
                        apt.dentist_id.name))

    @api.model
    def _booked_slots(self, dentist_id, date_val):
        rows = self.search_read([
            ('dentist_id', '=', dentist_id),
            ('appointment_date', '=', date_val),
            ('state', '!=', 'cancelled'),
            ('booking_slot', '>', 0),
        ], ['booking_slot'])
        return {r['booking_slot'] for r in rows}

    @api.model
    def get_available_slots(self, dentist_id, date_val):
        """Free 30-min slots for one dentist on one date.

        Slots = dentist shift ranges, stepped by SLOT_HOURS, minus slots
        already booked, minus past times when the date is today (clinic TZ).
        Returns a list of floats (slot start hours), sorted.
        """
        dentist = self.env['hr.employee'].browse(dentist_id)
        if not dentist.exists():
            return []
        now_clinic = datetime.now(timezone.utc) + timedelta(
            hours=BAGHDAD_UTC_OFFSET)
        cutoff = -1.0
        if date_val == now_clinic.date():
            cutoff = now_clinic.hour + now_clinic.minute / 60.0
        booked = self._booked_slots(dentist_id, date_val)
        slots = []
        for shift in dentist.time_shift_ids:
            start, end = shift.start_time or 0.0, shift.end_time or 0.0
            t = start
            while t + SLOT_HOURS <= end + 1e-6:
                if t > cutoff and t not in booked:
                    slots.append(t)
                t += SLOT_HOURS
        return sorted(set(slots))

    @api.model
    def get_slot_map(self, date_val, dentist_id=None):
        """Public-booking payload: [{value, label, dentist_id}] —
        aggregated across all dentists when none is chosen (first free
        dentist wins each time)."""
        if dentist_id:
            dentists = self.env['hr.employee'].browse(dentist_id)
        else:
            dentists = self.env['hr.employee'].search(
                [('is_dentist', '=', True)])
        by_time = {}
        for dentist in dentists:
            for slot in self.get_available_slots(dentist.id, date_val):
                by_time.setdefault(slot, dentist.id)
        return [
            {'value': t, 'label': _fmt(t), 'dentist_id': d}
            for t, d in sorted(by_time.items())
        ]

    @api.model
    def _shift_for_slot(self, dentist_id, slot):
        """The dentist shift containing a slot start time."""
        dentist = self.env['hr.employee'].browse(dentist_id)
        for shift in dentist.time_shift_ids:
            if (shift.start_time or 0.0) - 1e-6 <= slot < (shift.end_time or 0.0):
                return shift
        return self.env['dental.time.shift']
