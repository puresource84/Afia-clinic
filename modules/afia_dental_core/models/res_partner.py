# -*- coding: utf-8 -*-
"""Patient extension of res.partner. Clean-room rewrite (2026-08)."""
from datetime import date

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_patient = fields.Boolean(string='Is a Patient', default=False, index=True)
    patient_no = fields.Char(string='Patient No.', copy=False, index=True)
    company_type = fields.Selection(selection_add=[
        ('person', 'Patient'),
        ('company', 'Medicine Distributor'),
    ])

    dob = fields.Date(string='Date of Birth')
    patient_age = fields.Integer(
        string='Age', compute='_compute_patient_age', store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')

    medical_questionnaire_ids = fields.One2many(
        'medical.questionnaire', 'patient_id', string='Medical Questionnaire')
    appointment_ids = fields.One2many(
        'dental.appointment', 'patient_id', string='Appointments')
    appointment_count = fields.Integer(compute='_compute_appointment_count')
    report_ids = fields.One2many(
        'xray.report', 'patient_id', string='X-Ray Reports')
    medical_alert_summary = fields.Char(
        string='Medical Alerts', compute='_compute_medical_alert_summary',
        help='Questions answered "Yes" on the Medical Questionnaire tab — '
             'surfaced here so front-desk staff see it without opening the '
             'tab. Added 2026-08-24 to use the empty space next to Patient '
             'Details instead of burying this in a tab.')

    @api.depends('medical_questionnaire_ids.yes_no', 'medical_questionnaire_ids.question_id')
    def _compute_medical_alert_summary(self):
        for partner in self:
            flagged = partner.medical_questionnaire_ids.filtered(
                lambda q: q.yes_no == 'yes')
            partner.medical_alert_summary = ', '.join(
                flagged.mapped('question_id.name')) if flagged else False

    @api.depends('dob')
    def _compute_patient_age(self):
        today = date.today()
        for partner in self:
            if partner.dob:
                dob = partner.dob
                partner.patient_age = today.year - dob.year - (
                    (today.month, today.day) < (dob.month, dob.day))
            else:
                partner.patient_age = 0

    def _compute_appointment_count(self):
        # One read_group for the whole recordset instead of a search_count
        # per record.
        groups = self.env['dental.appointment']._read_group(
            [('patient_id', 'in', self.ids)], ['patient_id'], ['__count'])
        counts = {partner.id: count for partner, count in groups}
        for partner in self:
            partner.appointment_count = counts.get(partner.id, 0)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """2026-08-26 fix: this used to `return self._search(args, limit=limit)`
        — `_search()` returns a raw Query object (or bare ids), NOT the list
        of (id, display_name) tuples that `name_search` callers require.
        Every partner autocomplete across the ENTIRE app (Contacts, invoices,
        appointment patient picker, calendar attendees, etc.) that fell
        through to this method for a non-empty search term was silently
        getting a Query object back instead of results — surfaced to the
        user as a generic "UncaughtPromiseError" in the widget JS the moment
        it tried to read `.length`/iterate over it. Root-caused via
        dental_ux_fixes.name_search's patient_no fast-path calling
        super().name_search() and landing here whenever the term didn't
        match a patient number (e.g. searching a dentist/staff name in the
        calendar attendees field). Fixed by using `search()` (returns a
        recordset) and mapping to proper (id, display_name) tuples, exactly
        like the base implementation does. See
        project_afia_partner_name_search_fix_2026-08-26 memory.
        """
        args = list(args or [])
        if name:
            domain = ['|', ('name', operator, name), ('patient_no', operator, name)] + args
            partners = self.search(domain, limit=limit)
            return [(p.id, p.display_name) for p in partners]
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        new_patients = records.filtered('is_patient')
        self._onboard_new_patients(new_patients)
        return records

    def write(self, vals):
        # A partner can also become a patient later — e.g. auto-flagged by
        # account.move._sync_patient_flag() when a treatment invoice is
        # created for a contact that wasn't made through the Patients app's
        # own "New" button. Run the same onboarding (patient number,
        # medical questionnaire) that create() does, but only for partners
        # that are newly becoming a patient here.
        newly_flagged = self.env['res.partner']
        if vals.get('is_patient'):
            newly_flagged = self.filtered(lambda p: not p.is_patient)
        res = super().write(vals)
        if newly_flagged:
            self._onboard_new_patients(newly_flagged)
        return res

    def _onboard_new_patients(self, patients):
        for record in patients:
            if not record.patient_no:
                record.patient_no = self.env['ir.sequence'].next_by_code(
                    'dental.patient') or _('New')
        if patients:
            # sudo: receptionists may create patients but (once
            # dental_clinical_permissions is installed) have no create
            # right on the clinical questionnaire rows seeded here.
            Questionnaire = self.env['medical.questionnaire'].sudo()
            questions = self.env['medical.questions'].sudo().search([('active', '=', True)])
            Questionnaire.create([
                {'patient_id': p.id, 'question_id': q.id}
                for p in patients for q in questions
                if not Questionnaire.search_count(
                    [('patient_id', '=', p.id), ('question_id', '=', q.id)])
            ])

    def action_view_appointments(self):
        # 2026-09-20: this was previously duplicated (with a slightly
        # different context) in dental_ux_fixes/models/res_partner_smart_buttons.py,
        # which loaded after this module and silently won at runtime — see
        # afia_dental_core/.spec/bugs/afia_dental_core-duplicate-appointment-button/.
        # That copy is removed; this is now the single authoritative
        # implementation. search_default_patient_id is carried over from
        # the removed copy (redundant with the domain below, but harmless
        # and preserves prior behavior exactly).
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Appointments'),
            'res_model': 'dental.appointment',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {
                'default_patient_id': self.id,
                'search_default_patient_id': self.id,
            },
        }

    def action_prescription(self):
        self.ensure_one()
        Prescription = self.env['dental.prescription']
        prescriptions = Prescription.search([('patient_id', '=', self.id)])
        latest_appointment = self.env['dental.appointment'].search(
            [('patient_id', '=', self.id)], order='start_datetime desc', limit=1)

        if prescriptions:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Prescriptions'),
                'view_mode': 'list,form',
                'res_model': 'dental.prescription',
                'domain': [('id', 'in', prescriptions.ids)],
                'context': {'default_patient_id': self.id},
            }
        prescription = Prescription.create({
            'appointment_id': latest_appointment.id if latest_appointment else False,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Prescription'),
            'view_mode': 'form',
            'res_model': 'dental.prescription',
            'res_id': prescription.id,
        }

    def action_open_patient_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Patient Payments'),
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'search_default_partner_id': self.id},
        }
