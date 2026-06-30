"""
dental.soap.note — one structured clinical note per appointment visit.

S/O/A/P sections are now driven by a content library (dental.soap.sentence).
Dentists select phrases via autocomplete; new phrases are saved to the library
automatically (organic growth). Free-text fields have been replaced by
Many2many sentence tags.

Life-cycle:
  draft  →  [Sign]  →  signed
  Once signed, the note is read-only for dentists.
  Only base.group_system (Superadmin) can reset a signed note.
"""
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class DentalSoapNote(models.Model):
    _name = 'dental.soap.note'
    _description = 'SOAP Clinical Note'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'note_date desc, id desc'
    _rec_name = 'display_name'

    # ── Identity ──────────────────────────────────────────────────────────────
    display_name = fields.Char(
        string='Reference', compute='_compute_display_name', store=True)

    appointment_id = fields.Many2one(
        'dental.appointment', string='Appointment',
        required=True, ondelete='cascade', index=True)

    patient_id = fields.Many2one(
        'res.partner', string='Patient',
        related='appointment_id.patient_id', store=True, readonly=True)

    dentist_id = fields.Many2one(
        'hr.employee', string='Dentist',
        related='appointment_id.dentist_id', store=True, readonly=True)

    note_date = fields.Date(
        string='Visit Date',
        related='appointment_id.appointment_date', store=True, readonly=True)

    template_id = fields.Many2one(
        'dental.soap.template', string='Apply Template',
        help='Select a procedure template to pre-fill this note. '
             'Replaces any currently selected content library entries.')

    # ── Subjective ────────────────────────────────────────────────────────────
    chief_complaint = fields.Char(
        string='Chief Complaint', tracking=True,
        help="The patient's main reason for the visit in their own words.")

    s_ids = fields.Many2many(
        'dental.soap.sentence',
        'soap_note_s_rel', 'note_id', 'sentence_id',
        string='Subjective',
        domain=[('section', '=', 'S')],
        help='Select phrases from the content library or type new ones to add.')

    # ── Objective ─────────────────────────────────────────────────────────────
    tooth_ids = fields.Many2many(
        'dental.tooth', 'soap_note_tooth_rel', 'note_id', 'tooth_id',
        string='Teeth Involved')
    vital_signs = fields.Char(
        string='Vital Signs',
        help='BP, pulse, SpO₂ — only if relevant (e.g. sedation cases).')

    o_ids = fields.Many2many(
        'dental.soap.sentence',
        'soap_note_o_rel', 'note_id', 'sentence_id',
        string='Objective',
        domain=[('section', '=', 'O')],
        help='Select examination findings or type new ones to add.')

    # ── Assessment ────────────────────────────────────────────────────────────
    cdt_codes = fields.Char(
        string='CDT / Procedure Codes',
        help='Comma-separated CDT codes for this visit (e.g. D7140, D0220).')

    a_ids = fields.Many2many(
        'dental.soap.sentence',
        'soap_note_a_rel', 'note_id', 'sentence_id',
        string='Assessment',
        domain=[('section', '=', 'A')],
        help='Select diagnosis/assessment statements or type new ones.')

    # ── Plan ──────────────────────────────────────────────────────────────────
    p_ids = fields.Many2many(
        'dental.soap.sentence',
        'soap_note_p_rel', 'note_id', 'sentence_id',
        string='Plan',
        domain=[('section', '=', 'P')],
        help='Select treatment plan / next-step entries or type new ones.')

    # ── Signature & lock ──────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Draft'),
        ('signed', 'Signed'),
    ], default='draft', string='Status', required=True,
       tracking=True, copy=False)

    signed_by = fields.Many2one(
        'res.users', string='Signed By', readonly=True,
        copy=False, tracking=True)
    signed_date = fields.Datetime(
        string='Signed On', readonly=True, copy=False, tracking=True)

    is_locked = fields.Boolean(
        string='Locked', compute='_compute_is_locked',
        help='True once signed AND 24 hours have elapsed.')

    # ── Computed ──────────────────────────────────────────────────────────────
    @api.depends('appointment_id', 'note_date')
    def _compute_display_name(self):
        for note in self:
            appt = note.appointment_id
            ref = appt.appointment_no or f'#{appt.id}' if appt else '?'
            date = note.note_date or fields.Date.today()
            note.display_name = f'Note — {ref} — {date}'

    @api.depends('state', 'signed_date')
    def _compute_is_locked(self):
        now = fields.Datetime.now()
        for note in self:
            if note.state == 'signed' and note.signed_date:
                note.is_locked = (now - note.signed_date) >= timedelta(hours=24)
            else:
                note.is_locked = False

    # ── Template application ───────────────────────────────────────────────────
    @api.onchange('template_id')
    def _onchange_template_id(self):
        tmpl = self.template_id
        if not tmpl:
            return
        Sentence = self.env['dental.soap.sentence']
        self.chief_complaint = tmpl.chief_complaint or self.chief_complaint
        self.cdt_codes = tmpl.cdt_codes or self.cdt_codes
        self.s_ids = Sentence.search(
            [('template_id', '=', tmpl.id), ('section', '=', 'S')])
        self.o_ids = Sentence.search(
            [('template_id', '=', tmpl.id), ('section', '=', 'O')])
        self.a_ids = Sentence.search(
            [('template_id', '=', tmpl.id), ('section', '=', 'A')])
        self.p_ids = Sentence.search(
            [('template_id', '=', tmpl.id), ('section', '=', 'P')])
        return {'warning': {
            'title': 'Template Applied',
            'message': (f'Pre-filled from "{tmpl.name}". '
                        'Add, remove or type new entries in each section.'),
        }}

    # ── ORM write / unlink guards ─────────────────────────────────────────────
    # These enforce the lock at the database layer, not just the UI.
    # Superadmin (base.group_system) bypasses the guard so action_reset_draft
    # can still clear the note.
    _LOCK_EXEMPT_FIELDS = frozenset({'message_main_attachment_id'})

    def write(self, vals):
        if not self.env.user.has_group('base.group_system'):
            for note in self:
                if note.is_locked:
                    changed = set(vals) - self._LOCK_EXEMPT_FIELDS
                    if changed:
                        raise UserError(
                            'Clinical note "%s" is locked (signed > 24 h ago) '
                            'and cannot be edited. Contact your system '
                            'administrator.' % note.display_name)
        return super().write(vals)

    def unlink(self):
        if not self.env.user.has_group('base.group_system'):
            locked = self.filtered('is_locked')
            if locked:
                raise UserError(
                    'Cannot delete a locked clinical note: %s'
                    % ', '.join(locked.mapped('display_name')))
        return super().unlink()

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_sign(self):
        """Dentist signs off the note. After 24 h it becomes read-only."""
        for note in self:
            if note.state == 'signed':
                raise UserError('This note is already signed.')
            note.write({
                'state': 'signed',
                'signed_by': self.env.user.id,
                'signed_date': fields.Datetime.now(),
            })
            note.message_post(
                body=f'Note signed by {self.env.user.name}. '
                     f'It will become locked 24 hours from now.')

    def action_reset_draft(self):
        """Superadmin only — reset a signed note back to draft."""
        if not self.env.user.has_group('base.group_system'):
            raise UserError(
                'Only a system administrator can reopen a signed clinical note.')
        for note in self:
            note.write({'state': 'draft', 'signed_by': False, 'signed_date': False})
            note.message_post(body='Note reset to Draft by Admin.')

    def action_print_soap_note(self):
        """Print PDF report for this SOAP note."""
        return self.env.ref(
            'dental_soap_notes.action_report_soap_note'
        ).report_action(self)


class DentalAppointmentSoapButton(models.Model):
    """Adds a soap_note_count field + action to dental.appointment."""
    _inherit = 'dental.appointment'

    soap_note_ids = fields.One2many(
        'dental.soap.note', 'appointment_id', string='Clinical Notes')
    soap_note_count = fields.Integer(
        string='Notes', compute='_compute_soap_note_count')

    @api.depends('soap_note_ids')
    def _compute_soap_note_count(self):
        for appt in self:
            appt.soap_note_count = len(appt.soap_note_ids)

    def action_open_soap_notes(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Clinical Notes',
            'res_model': 'dental.soap.note',
            'view_mode': 'list,form',
            'domain': [('appointment_id', '=', self.id)],
            'context': {
                'default_appointment_id': self.id,
                'default_template_id': False,
            },
        }
        if self.soap_note_count == 1:
            action['view_mode'] = 'form'
            action['res_id'] = self.soap_note_ids[0].id
        return action
