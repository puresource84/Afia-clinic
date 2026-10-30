from odoo import api, fields, models


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

    # Availability (overlaps, shifts, leaves, past times, clinic timezone)
    # and the hard double-booking constraint live in afia_dental_core's
    # dental.appointment.get_available_slots / _check_dentist_double_booking.
    # Staff-booked appointments with booking_slot = 0 are now seen too.

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
