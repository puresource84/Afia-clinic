# -*- coding: utf-8 -*-
"""Prescriptions. Clean-room rewrite (2026-08)."""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DentalPrescription(models.Model):
    _name = 'dental.prescription'
    _description = 'Dental Prescription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence_no'
    _order = 'prescription_date desc'

    sequence_no = fields.Char(
        string='Sequence No', required=True, readonly=True, copy=False,
        default=lambda self: _('New'))
    appointment_id = fields.Many2one(
        'dental.appointment', string='Appointment', required=True)
    patient_id = fields.Many2one(
        related='appointment_id.patient_id', string='Patient', store=True, readonly=True)
    prescribed_doctor_id = fields.Many2one(
        related='appointment_id.dentist_id', string='Prescribed Doctor', store=True, readonly=True)
    referred_dentist_id = fields.Many2one(
        'hr.employee', string='Referred Dentist', domain="[('is_dentist', '=', True)]",
        help='Choose a different dentist when referring the patient onward.')

    treatment_id = fields.Many2one('dental.treatment', string='Treatment')
    cost = fields.Float(related='treatment_id.cost', string='Treatment Cost', readonly=True)
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id, required=True)

    prescription_date = fields.Date(default=fields.Date.context_today, required=True)
    next_appointment_date = fields.Date(string='Next Appointment Date')
    selected_teeth = fields.Char(string='Selected Teeth')

    state = fields.Selection([
        ('new', 'New'),
        ('done', 'Prescribed'),
        ('invoiced', 'Invoiced'),
    ], default='new', tracking=True)

    medicine_ids = fields.One2many('dental.prescription_lines', 'prescription_id', string='Medicines')
    treatment_invoice_id = fields.Many2one('account.move', string='Treatment Invoice', readonly=True)
    prescription_invoice_id = fields.Many2one('account.move', string='Prescription Invoice', readonly=True)

    # -- CRUD -------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('sequence_no', _('New')) == _('New'):
                vals['sequence_no'] = self.env['ir.sequence'].next_by_code(
                    'dental.prescriptions') or _('New')
        records = super().create(vals_list)
        records._reschedule_next_visit()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'next_appointment_date' in vals or 'referred_dentist_id' in vals:
            self._reschedule_next_visit()
        return res

    def _reschedule_next_visit(self):
        """If a next-appointment date is set, either move the patient's
        already-scheduled upcoming appointment to it, or create a new
        draft appointment. Never touches an appointment already in
        progress today."""
        for rec in self:
            if not rec.next_appointment_date or not rec.patient_id:
                continue
            dentist = rec.referred_dentist_id or rec.prescribed_doctor_id
            if not dentist:
                continue

            Appointment = self.env['dental.appointment']
            upcoming = Appointment.search([
                ('patient_id', '=', rec.patient_id.id),
                ('appointment_date', '>=', fields.Date.context_today(rec)),
                ('state', 'not in', ('done', 'cancelled')),
            ], order='start_datetime asc', limit=1)

            next_start = fields.Datetime.to_datetime(rec.next_appointment_date)
            if upcoming and upcoming.appointment_date != fields.Date.context_today(rec):
                upcoming.write({'start_datetime': next_start, 'dentist_id': dentist.id})
            else:
                Appointment.create({
                    'patient_id': rec.patient_id.id,
                    'dentist_id': dentist.id,
                    'start_datetime': next_start,
                    'state': 'draft',
                })

    # -- Actions ------------------------------------------------------
    def action_prescribed(self):
        for rec in self:
            rec.state = 'done'
            apt = rec.appointment_id
            if apt and apt.state not in ('done', 'cancelled'):
                # Use the real workflow so hooks on action_done run
                # (consumable stock deduction, recall date, end time).
                if apt.state == 'draft':
                    apt.action_confirm()
                apt.action_done()

    def _get_treatment_income_account(self):
        """Dental treatments aren't backed by a product.template, so
        Odoo's usual product -> income-account lookup has nothing to go
        on for the treatment line. Fall back to the company's sales
        journal default account, which every journal is guaranteed to
        have (see account.journal._create_default_account /
        default_account_id)."""
        self.ensure_one()
        company = self.env.company
        journal = self.env['account.journal'].search([
            *self.env['account.journal']._check_company_domain(company),
            ('type', '=', 'sale'),
        ], limit=1)
        return journal.default_account_id

    def action_create_invoice(self):
        self.ensure_one()
        if not self.treatment_id:
            raise UserError(_('Select a treatment before invoicing.'))

        income_account = self._get_treatment_income_account()
        if not income_account:
            raise UserError(_(
                'No income account is configured for the sales journal. '
                'Set one up in Accounting before invoicing treatments.'))

        treatment_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.id,
            'is_treatment_invoice': True,
            'invoice_line_ids': [(0, 0, {
                'name': self.treatment_id.name,
                'quantity': 1,
                'price_unit': self.cost,
                'account_id': income_account.id,
            })],
        })

        medicine_lines = []
        for line in self.medicine_ids:
            product = line.medicament_id.product_variant_id
            if not product:
                continue
            medicine_lines.append((0, 0, {
                'product_id': product.id,
                'name': line.display_name,
                'quantity': line.quantity,
                'price_unit': line.price,
            }))
        prescription_invoice = False
        if medicine_lines:
            prescription_invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.patient_id.id,
                'invoice_line_ids': medicine_lines,
            })

        self.write({
            'treatment_invoice_id': treatment_invoice.id,
            'prescription_invoice_id': prescription_invoice.id if prescription_invoice else False,
            'state': 'invoiced',
        })

        invoice_ids = [treatment_invoice.id] + ([prescription_invoice.id] if prescription_invoice else [])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Treatment & Prescription Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoice_ids)],
        }

    def action_print_prescription(self):
        return self.env.ref('afia_dental_core.report_pdf_dental_prescription').report_action(self)


class DentalPrescriptionLines(models.Model):
    _name = 'dental.prescription_lines'
    _description = 'Dental Prescription Line'
    _rec_name = 'medicament_id'

    prescription_id = fields.Many2one('dental.prescription', required=True, ondelete='cascade')
    medicament_id = fields.Many2one(
        'product.template', string='Medicament', domain="[('is_medicine', '=', True)]")
    generic_name = fields.Char(related='medicament_id.generic_name', readonly=True)
    dosage_strength = fields.Integer(related='medicament_id.dosage_strength', readonly=True)
    medicament_form = fields.Selection([
        ('tablet', 'Tablets'),
        ('capsule', 'Capsules'),
        ('liquid', 'Liquid'),
        ('injection', 'Injections'),
    ], required=True)
    frequency_id = fields.Many2one('medicine.frequency', string='Frequency')
    quantity = fields.Integer(default=1, required=True)
    price = fields.Float(related='medicament_id.list_price', readonly=True)
    morning = fields.Boolean()
    noon = fields.Boolean(string='Afternoon')
    night = fields.Boolean()
    medicine_take = fields.Selection([
        ('before', 'Before Food'),
        ('after', 'After Food'),
    ], default='after')
    days = fields.Float()
