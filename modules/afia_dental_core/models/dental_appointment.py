# -*- coding: utf-8 -*-
"""Dental appointment — the scheduling hub of the Afia Dental Clinic suite.

Clean-room rewrite (2026-08). Field/model technical names and the
`state` selection keys are preserved exactly for compatibility with every
other Afia Dental Clinic module (see PACKAGE_MANIFEST.md dependency
analysis — dental.appointment is referenced by all 34 companion modules).
Internals are new: appointments are backed by a real calendar.event so
dentists get a proper calendar, capacity checks and ICS export, instead
of a bespoke date-only field with denormalized patient data copied onto
every row.
"""
import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DentalAppointment(models.Model):
    _name = 'dental.appointment'
    _description = 'Dental Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'appointment_no'
    _order = 'start_datetime desc'

    # -- Identity -----------------------------------------------------
    appointment_no = fields.Char(
        string='Appointment No.', readonly=True, copy=False,
        default=lambda self: _('New'))
    company_id = fields.Many2one(
        'res.company', string='Clinic', required=True,
        default=lambda self: self.env.company, index=True)

    # -- Who ------------------------------------------------------------
    patient_id = fields.Many2one(
        'res.partner', string='Patient', required=True, tracking=True,
        domain="[('is_patient', '=', True)]")
    dentist_id = fields.Many2one(
        'hr.employee', string='Dentist', required=True, tracking=True,
        domain="[('is_dentist', '=', True)]")
    user_id = fields.Many2one(
        'res.users', string='Responsible',
        default=lambda self: self.env.user)
    # Kept for backward compatibility — several companion modules and
    # reports still read the plain name string rather than user_id.
    user_name = fields.Char(
        string='Responsible Name', compute='_compute_user_name', store=True)

    # -- Patient snapshot, now live instead of copy/pasted --------------
    patient_no = fields.Char(related='patient_id.patient_no', string='Patient No.', readonly=True)
    gender = fields.Selection(related='patient_id.gender', string='Gender', readonly=True)
    age = fields.Integer(related='patient_id.patient_age', string='Age', readonly=True)
    mobile = fields.Char(related='patient_id.mobile', string='Mobile', readonly=True)

    # -- When -------------------------------------------------------------
    start_datetime = fields.Datetime(
        string='Start', required=True, tracking=True,
        default=fields.Datetime.now)
    duration = fields.Float(
        string='Duration (hours)', default=0.5,
        help='Expected chair time for this appointment.')
    stop_datetime = fields.Datetime(
        string='End', compute='_compute_stop_datetime', store=True)
    # Date-only projection kept for every companion module / report that
    # filters or groups appointments by calendar day.
    #
    # 2026-08: tried giving this an `inverse=` so a bare datepicker could
    # move the day directly. Reverted — on this Odoo build, stored fields
    # that combine `compute` + `inverse` silently never re-run on
    # dependency changes (verified empirically: a plain `store=True`
    # compute-only sibling field recomputed correctly on the same write,
    # while compute+inverse fields stayed frozen at their initial value
    # with fields_get() even reporting an empty `depends` list for them).
    # Root cause not tracked down further; explicit write()-time sync
    # below is the reliable alternative and doesn't depend on that
    # mechanism at all. UI edits already work regardless, since Owl forms
    # fire onchange on any field edit independent of a Python inverse.
    appointment_date = fields.Date(
        string='Date', compute='_compute_appointment_date',
        store=True, index=True, readonly=True)
    calendar_event_id = fields.Many2one(
        'calendar.event', string='Calendar Entry', copy=False, readonly=True,
        help='Linked Odoo Calendar entry, kept in sync automatically so '
             'dentists see appointments on their normal calendar with '
             'reminders, ICS export and conflict checks.')

    urgency = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
    ], string='Treatment Type', default='normal')
    patient_categ = fields.Selection([
        ('old', 'Returning'),
        ('new', 'New'),
    ], string='Patient Category')

    tooth_ids = fields.Many2many('dental.tooth', string='Teeth Affected')
    treatments = fields.Many2many('dental.treatment', string='Treatments')

    # Legacy shift metadata — kept for modules that still schedule by
    # named block (e.g. dental_booking_slots) rather than exact datetime.
    time_shift_ids = fields.Many2many(
        'dental.time.shift', string='Available Times',
        compute='_compute_time_shifts')
    shift_id = fields.Many2one(
        'dental.time.shift', string='Booking Time',
        domain="[('id', 'in', time_shift_ids)]")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, index=True)

    patient_notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('duration_positive', 'CHECK(duration > 0)',
         'Appointment duration must be greater than zero.'),
    ]

    # -- Compute ------------------------------------------------------
    @api.depends('start_datetime', 'duration')
    def _compute_stop_datetime(self):
        for rec in self:
            if rec.start_datetime and rec.duration:
                rec.stop_datetime = fields.Datetime.add(
                    rec.start_datetime, hours=rec.duration)
            else:
                rec.stop_datetime = rec.start_datetime

    @api.depends('start_datetime')
    def _compute_appointment_date(self):
        for rec in self:
            rec.appointment_date = fields.Date.context_today(
                rec, timestamp=rec.start_datetime) if rec.start_datetime else False

    def _shift_start_datetime_to_date(self, new_date):
        """Move start_datetime to new_date, keeping time-of-day (user tz).
        Explicit helper used by write() below instead of a field inverse —
        see the note on appointment_date's definition for why."""
        self.ensure_one()
        if self.start_datetime:
            local = fields.Datetime.context_timestamp(self, self.start_datetime)
            new_local = local.replace(
                year=new_date.year, month=new_date.month, day=new_date.day)
            self.start_datetime = new_local.astimezone(pytz.utc).replace(tzinfo=None)
        else:
            self.start_datetime = fields.Datetime.to_datetime(new_date)

    @api.depends('user_id')
    def _compute_user_name(self):
        for rec in self:
            rec.user_name = rec.user_id.name or self.env.user.name

    @api.depends('dentist_id')
    def _compute_time_shifts(self):
        # Batched: one search for the whole recordset instead of one
        # search() per record.
        all_shift_ids = self.mapped('dentist_id.time_shift_ids').ids
        valid_shift_ids = set(self.env['dental.time.shift'].search(
            [('id', 'in', all_shift_ids)]).ids)
        for rec in self:
            rec.time_shift_ids = [
                sid for sid in rec.dentist_id.time_shift_ids.ids
                if sid in valid_shift_ids
            ]

    # -- CRUD -----------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('appointment_no', _('New')) == _('New') or not vals.get('appointment_no'):
                vals['appointment_no'] = self.env['ir.sequence'].next_by_code(
                    'dental.appointment') or _('New')
            if vals.get('patient_id'):
                self._ensure_patient_no(vals['patient_id'])
        records = super().create(vals_list)
        records._sync_calendar_event()
        return records

    def write(self, vals):
        # A caller moving the day via appointment_date directly (rather than
        # start_datetime) — explicit sync in place of a field inverse; see
        # the note on appointment_date's definition. appointment_date is a
        # compute-only stored field (no inverse), so it must be popped out
        # of vals — the ORM rejects direct writes to compute-only fields —
        # and re-derives itself once start_datetime is shifted below.
        if 'appointment_date' in vals and 'start_datetime' not in vals:
            new_date = fields.Date.to_date(vals.pop('appointment_date'))
            for rec in self:
                rec._shift_start_datetime_to_date(new_date)
        res = super().write(vals)
        if any(f in vals for f in (
                'start_datetime', 'duration', 'dentist_id', 'patient_id',
                'state', 'patient_notes')):
            self._sync_calendar_event()
        return res

    def unlink(self):
        events = self.calendar_event_id
        res = super().unlink()
        events.unlink()
        return res

    def _ensure_patient_no(self, patient_id):
        patient = self.env['res.partner'].browse(patient_id)
        if patient and not patient.patient_no:
            patient.patient_no = self.env['ir.sequence'].next_by_code(
                'dental.patient') or _('New')

    # -- Calendar bridge --------------------------------------------------
    def _calendar_event_values(self):
        self.ensure_one()
        dentist_user = self.dentist_id.user_id
        partner_ids = self.dentist_id.work_contact_id.ids
        if self.patient_id:
            partner_ids = list(set(partner_ids + self.patient_id.ids))
        return {
            'name': _('%(patient)s with Dr. %(dentist)s', patient=self.patient_id.name,
                       dentist=self.dentist_id.name),
            'start': self.start_datetime,
            'stop': self.stop_datetime,
            'duration': self.duration,
            'description': self.patient_notes or '',
            'partner_ids': [(6, 0, partner_ids)],
            'user_id': dentist_user.id if dentist_user else self.env.uid,
            'res_model': 'dental.appointment',
            'res_id': self.id,
            'show_as': 'busy' if self.state != 'cancelled' else 'free',
            'active': self.state != 'cancelled',
        }

    def _sync_calendar_event(self):
        Calendar = self.env['calendar.event'].sudo()
        for rec in self:
            if not rec.start_datetime or not rec.dentist_id or not rec.patient_id:
                continue
            values = rec._calendar_event_values()
            if rec.calendar_event_id:
                rec.calendar_event_id.write(values)
            else:
                rec.calendar_event_id = Calendar.create(values)

    # -- Workflow ---------------------------------------------------------
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_start(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(_('Only confirmed appointments can be started.'))
            rec.state = 'in_progress'

    def action_open_patient_form(self):
        self.ensure_one()
        if self.state == 'confirmed':
            self.state = 'in_progress'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Patient'),
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.patient_id.id,
            'target': 'current',
        }

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
