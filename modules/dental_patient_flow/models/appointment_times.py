"""dental_appointment_times: HH:MM time fields, shift restriction, treatment duration."""
import logging
from datetime import datetime as dt

import pytz

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

_CLINIC_TZ = 'Asia/Baghdad'


def _fmt(hours_float):
    """Format float hours as HH:MM string for error messages."""
    h = int(hours_float)
    m = int(round((hours_float - h) * 60))
    return f"{h:02d}:{m:02d}"


class DentalTreatmentDuration(models.Model):
    """Add a configurable default duration to each treatment type."""
    _inherit = 'dental.treatment'

    default_duration = fields.Float(
        string='Default Duration (h)',
        digits=(4, 2),
        default=0.0,
        help='Default appointment duration in decimal hours (0.75 = 45 min). '
             'Leave 0 to skip auto-fill.',
    )


class DentalAppointmentTimes(models.Model):
    _inherit = 'dental.appointment'

    # -- Primary Datetime fields (calendar date_start / date_stop) --
    #
    # 2026-08: afia_dental_core's clean-room rewrite made start_datetime
    # (backed by a real calendar.event) the single source of truth for
    # scheduling. apt_start/apt_end used to be their own independently
    # stored fields here, which meant an appointment booked through the
    # core calendar view never touched them (no shift/double-booking
    # checks ran, and the HH:MM fields showed nothing), while one booked
    # through this module's HH:MM UI never updated start_datetime (wrong
    # slot on the real Odoo Calendar, calendar.event never synced) — two
    # disconnected clocks on the same record.
    #
    # First attempt: turn apt_start/apt_end into a compute+inverse alias
    # over start_datetime/stop_datetime. Reverted — on this Odoo build,
    # stored fields combining compute+inverse silently never re-run on
    # dependency changes (verified: a plain store=True compute-only
    # sibling field, e.g. apt_duration below, recomputes correctly on the
    # exact same kind of write; fields_get() even reports an empty
    # `depends` list for the compute+inverse ones). Root cause not tracked
    # down further. Fixed instead with explicit two-way sync in create()/
    # write() below — plain writable fields, no framework magic, so it
    # can't silently stop working the same way.
    apt_start = fields.Datetime(string='Start Datetime', copy=False)
    apt_end = fields.Datetime(string='End Datetime', copy=False)

    # -- HH:MM float fields shown in the form --

    apt_start_time = fields.Float(
        string='Start Time',
        compute='_compute_apt_times',
        inverse='_inverse_apt_start_time',
        digits=(4, 2),
    )
    apt_end_time = fields.Float(
        string='End Time',
        compute='_compute_apt_times',
        inverse='_inverse_apt_end_time',
        digits=(4, 2),
    )

    # -- Duration (read-only, auto-calculated) --

    apt_duration = fields.Float(
        string='Duration',
        compute='_compute_apt_duration',
        store=True,
        readonly=True,
        digits=(4, 2),
    )

    # -- Defaults --
    #
    # 2026-08: this used to force appointment_date to today on every new
    # record. That was correct for the old architecture where
    # appointment_date was a plain required field, but in the clean-room
    # core it's a compute-only field derived from start_datetime (which
    # itself already defaults to now via afia_dental_core). Forcing a
    # stale "today" value here caused a serious bug: Odoo's create() flow
    # persists an explicitly-provided stored-computed field (appointment_date)
    # via a follow-up write({'appointment_date': ...}) call *without*
    # start_datetime in that vals dict — which is exactly the signature
    # core's write() uses to detect "the date picker was edited directly"
    # and re-anchor start_datetime to match. Net effect: creating an
    # appointment for a future date silently collapsed start_datetime back
    # to today (keeping only the time-of-day). Removed — the core already
    # defaults start_datetime sensibly and derives appointment_date from it.

    # -- Compute HH:MM from stored Datetime --

    @api.depends('apt_start', 'apt_end')
    def _compute_apt_times(self):
        for apt in self:
            if apt.apt_start:
                local = apt._to_local(apt.apt_start)
                apt.apt_start_time = local.hour + local.minute / 60.0
            else:
                apt.apt_start_time = 0.0
            if apt.apt_end:
                local = apt._to_local(apt.apt_end)
                apt.apt_end_time = local.hour + local.minute / 60.0
            else:
                apt.apt_end_time = 0.0

    # -- Inverse: HH:MM edit -> Datetime --

    def _inverse_apt_start_time(self):
        for apt in self:
            date = apt.appointment_date or fields.Date.context_today(apt)
            apt.apt_start = apt._float_to_utc(date, apt.apt_start_time)
            if not apt.apt_end or apt.apt_end <= apt.apt_start:
                apt.apt_end = apt._float_to_utc(date, apt.apt_start_time + 1.0)

    def _inverse_apt_end_time(self):
        for apt in self:
            date = apt.appointment_date or fields.Date.context_today(apt)
            apt.apt_end = apt._float_to_utc(date, apt.apt_end_time)

    # -- Duration --

    @api.depends('apt_start', 'apt_end')
    def _compute_apt_duration(self):
        for apt in self:
            if apt.apt_start and apt.apt_end and apt.apt_end > apt.apt_start:
                apt.apt_duration = (apt.apt_end - apt.apt_start).total_seconds() / 3600.0
            else:
                apt.apt_duration = 0.0

    # -- Onchange helpers --

    @api.onchange('apt_start')
    def _onchange_apt_start(self):
        if self.apt_start:
            self.appointment_date = self._to_local(self.apt_start).date()

    @api.onchange('apt_start_time', 'apt_end_time')
    def _onchange_apt_times_live(self):
        """Update Duration live; auto-push end time if at or before start."""
        if self.apt_end_time and self.apt_start_time:
            diff = self.apt_end_time - self.apt_start_time
            if diff <= 0:
                self.apt_end_time = self.apt_start_time + 1.0
                diff = 1.0
            self.apt_duration = diff
        else:
            self.apt_duration = 0.0

    @api.onchange('appointment_date')
    def _onchange_appointment_date(self):
        """Re-anchor apt_start / apt_end to the new date, keeping HH:MM."""
        if not self.appointment_date:
            return
        if self.apt_start:
            local = self._to_local(self.apt_start)
            self.apt_start = self._float_to_utc(
                self.appointment_date, local.hour + local.minute / 60.0)
        if self.apt_end:
            local = self._to_local(self.apt_end)
            self.apt_end = self._float_to_utc(
                self.appointment_date, local.hour + local.minute / 60.0)

    @api.onchange('treatments')
    def _onchange_treatments_duration(self):
        """Sum default_duration of selected treatments -> fill apt_duration + apt_end_time.

        Only acts when at least one treatment has a non-zero default_duration.
        The receptionist can still adjust times manually afterwards.
        """
        total = sum(t.default_duration for t in self.treatments if t.default_duration)
        if not total:
            return
        self.apt_duration = total
        if self.apt_start_time:
            self.apt_end_time = min(self.apt_start_time + total, 24.0)

    @api.onchange('apt_start_time', 'apt_end_time', 'dentist_id', 'apt_start', 'apt_end')
    def _onchange_shift_warning(self):
        """Non-blocking warning for shift violations and double-bookings."""
        msgs = []
        shift_msg = self._shift_violation_message()
        if shift_msg:
            msgs.append(shift_msg)
        db_msg = self._double_booking_message()
        if db_msg:
            msgs.append(db_msg)
        if msgs:
            return {'warning': {'title': 'Scheduling Conflict',
                                'message': '\n\n'.join(msgs)}}

    # -- Constraints --

    # NOTE: shift validation is NOT in @api.constrains because the calendar
    # pre-fills apt_start from the clicked slot BEFORE the apt_start_time inverse
    # runs to override it.  Using constrains would fire with the stale slot time
    # (e.g. 08:45) instead of the user-chosen time (e.g. 20:40), producing a
    # false validation error.  We validate in create() / write() instead, which
    # runs after ALL inverses have settled.

    @api.constrains('appointment_date')
    def _check_appointment_date_future(self):
        today = fields.Date.context_today(self)
        for apt in self:
            if apt.appointment_date and apt.appointment_date < today and apt.state == 'draft':
                raise ValidationError(
                    "Appointment date cannot be in the past. "
                    "Please select today or a future date."
                )

    # -- create() / write(): two-way scheduling sync + shift check --

    _SHIFT_TRIGGER_FIELDS = frozenset(
        {'apt_start', 'apt_end', 'apt_start_time', 'apt_end_time', 'dentist_id'}
    )

    def _sync_scheduling_fields(self, touched_apt=False, touched_core=False):
        """Keep apt_start/apt_end (this module's HH:MM UI + calendar) and
        start_datetime/duration/stop_datetime (core's calendar, the real
        source of truth) mirroring each other.

        Explicit two-way sync instead of a field compute/inverse — see the
        long note on apt_start's definition above for why. touched_apt/
        touched_core tell us which side the caller actually wrote to, so a
        plain unrelated write (e.g. state) doesn't do pointless work and,
        more importantly, so we don't ping-pong the two sides against each
        other. appointment_date (core, compute-only) doesn't need handling
        here — it derives from start_datetime on its own once that's set.
        """
        for apt in self:
            if touched_apt and not touched_core:
                vals = {}
                if apt.apt_start and apt.apt_start != apt.start_datetime:
                    vals['start_datetime'] = apt.apt_start
                if apt.apt_start and apt.apt_end and apt.apt_end > apt.apt_start:
                    new_duration = max(
                        (apt.apt_end - apt.apt_start).total_seconds() / 3600.0, 0.01)
                    if abs((apt.duration or 0.0) - new_duration) > 1e-6:
                        vals['duration'] = new_duration
                if vals:
                    super(DentalAppointmentTimes, apt).write(vals)
            else:
                vals = {}
                if apt.apt_start != apt.start_datetime:
                    vals['apt_start'] = apt.start_datetime
                if apt.apt_end != apt.stop_datetime:
                    vals['apt_end'] = apt.stop_datetime
                if vals:
                    super(DentalAppointmentTimes, apt).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for apt, vals in zip(records, vals_list):
            apt._sync_scheduling_fields(
                touched_apt='apt_start' in vals or 'apt_end' in vals,
                touched_core='start_datetime' in vals or 'duration' in vals,
            )
        for apt in records:
            msg = apt._shift_violation_message()
            if msg:
                _logger.warning('Appointment %s saved with shift violation: %s',
                                apt.appointment_no, msg)
            db_msg = apt._double_booking_message()
            if db_msg:
                _logger.warning('Appointment %s saved with double-booking: %s',
                                apt.appointment_no, db_msg)
        return records

    def write(self, vals):
        result = super().write(vals)
        touched_apt = 'apt_start' in vals or 'apt_end' in vals
        touched_core = 'start_datetime' in vals or 'duration' in vals
        if touched_apt or touched_core:
            self._sync_scheduling_fields(
                touched_apt=touched_apt, touched_core=touched_core)
        # Soft warnings — no hard block; onchange already alerted the user
        if self._SHIFT_TRIGGER_FIELDS & set(vals):
            for apt in self:
                msg = apt._shift_violation_message()
                if msg:
                    _logger.warning('Appointment %s shift violation: %s',
                                    apt.appointment_no, msg)
                db_msg = apt._double_booking_message()
                if db_msg:
                    _logger.warning('Appointment %s double-booking: %s',
                                    apt.appointment_no, db_msg)
        return result

    # -- Private helpers --

    def _shift_violation_message(self):
        """Return error text if self violates dentist shift windows, else None."""
        if not self.apt_start_time or not self.apt_end_time:
            return None
        if not self.dentist_id:
            return None
        shifts = self.dentist_id.time_shift_ids
        if not shifts:
            return None
        start, end = self.apt_start_time, self.apt_end_time
        if any(s.start_time <= start and end <= s.end_time for s in shifts):
            return None
        shift_desc = '  |  '.join(
            f"{_fmt(s.start_time)} - {_fmt(s.end_time)}" for s in shifts
        )
        return (
            f"The time {_fmt(start)} - {_fmt(end)} is outside "
            f"{self.dentist_id.name}'s working hours.\n"
            f"Configured shifts: {shift_desc}"
        )

    def _double_booking_message(self):
        """Return warning text if another confirmed appointment overlaps this one.

        During onchange, apt_start/apt_end may not yet be set even though
        apt_start_time and apt_end_time are, so we fall back to computing
        the datetimes inline from the float time + appointment_date.
        """
        if not self.dentist_id:
            return None

        # Resolve start/end datetimes — prefer stored Datetime; fall back to
        # computing from float time fields (onchange path).
        apt_start = self.apt_start
        apt_end = self.apt_end
        if (not apt_start or not apt_end) and self.apt_start_time and self.apt_end_time:
            date = self.appointment_date or fields.Date.context_today(self)
            apt_start = self._float_to_utc(date, self.apt_start_time)
            apt_end = self._float_to_utc(date, self.apt_end_time)

        if not apt_start or not apt_end:
            return None

        # Use _origin.id so new (unsaved) records don't match themselves
        exclude_id = self._origin.id if self._origin else (self.id or 0)
        domain = [
            ('dentist_id', '=', self.dentist_id.id),
            ('apt_start', '<', apt_end),
            ('apt_end', '>', apt_start),
            ('state', 'not in', ['cancelled', 'done']),
        ]
        if exclude_id:
            domain.append(('id', '!=', exclude_id))
        conflicts = self.env['dental.appointment'].search(domain, limit=3)
        if not conflicts:
            return None
        lines = '\n'.join(
            f"  • {c.appointment_no or 'Draft'} — {c.patient_id.name} "
            f"({c.apt_start.strftime('%H:%M')} – {c.apt_end.strftime('%H:%M')})"
            for c in conflicts
        )
        return (
            f"Double-booking detected for {self.dentist_id.name}:\n{lines}\n"
            f"You can still save — verify this is intentional."
        )

    def _float_to_utc(self, date, hours_float):
        tz_name = self.env.user.tz or _CLINIC_TZ
        try:
            tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            tz = pytz.timezone(_CLINIC_TZ)
        h = int(hours_float)
        m = int(round((hours_float - h) * 60))
        local_dt = tz.localize(dt(date.year, date.month, date.day, h, m, 0))
        return local_dt.astimezone(pytz.utc).replace(tzinfo=None)

    def _to_local(self, dt_utc):
        tz_name = self.env.user.tz or _CLINIC_TZ
        try:
            tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            tz = pytz.timezone(_CLINIC_TZ)
        if dt_utc.tzinfo is None:
            dt_utc = pytz.utc.localize(dt_utc)
        return dt_utc.astimezone(tz)
