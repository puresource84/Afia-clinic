from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DentalAppointmentInvoicing(models.Model):
    _inherit = 'dental.appointment'

    invoice_ids = fields.Many2many(
        'account.move',
        'dental_apt_invoice_rel',
        'appointment_id', 'invoice_id',
        string='Invoices',
        copy=False,
    )
    invoice_count = fields.Integer(
        string='Invoices',
        compute='_compute_invoice_count',
    )

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for apt in self:
            apt.invoice_count = len(apt.invoice_ids)

    def _get_active_invoices(self):
        self.ensure_one()
        return self.invoice_ids.filtered(lambda m: m.state != 'cancel')

    def _get_visit_invoice_line_vals(self):
        """One invoice per visit: the appointment's treatments, plus each
        linked prescription's treatment (unless already billed via the
        appointment) and its medicines."""
        self.ensure_one()
        product = self._get_dental_service_product()
        lines = [(0, 0, {
            'product_id': product.id,
            'name': treatment.name,
            'quantity': 1.0,
            'price_unit': treatment.cost,
        }) for treatment in self.treatments]
        prescriptions = self.env['dental.prescription'].search([
            ('appointment_id', '=', self.id), ('state', '!=', 'invoiced')])
        for rx in prescriptions:
            if rx.treatment_id and rx.treatment_id not in self.treatments:
                lines.append((0, 0, {
                    'product_id': product.id,
                    'name': rx.treatment_id.name,
                    'quantity': 1.0,
                    'price_unit': rx.cost,
                }))
            for line in rx.medicine_ids:
                medicine = line.medicament_id.product_variant_id
                if medicine:
                    lines.append((0, 0, {
                        'product_id': medicine.id,
                        'name': line.display_name,
                        'quantity': line.quantity,
                        'price_unit': line.price,
                    }))
        return lines, prescriptions

    def _create_visit_invoice(self):
        """Single entry point for billing a visit (appointment form, flow
        board and prescriptions all go through here), so the same treatment
        can never be invoiced twice."""
        self.ensure_one()
        if self._get_active_invoices():
            raise UserError(_('Appointment %s is already invoiced.')
                            % (self.appointment_no or self.id))
        if self.state != 'done':
            raise UserError(_('You can only invoice a completed appointment.'))
        line_vals, prescriptions = self._get_visit_invoice_line_vals()
        if not line_vals:
            raise UserError(_('No treatments are linked to this appointment.'))
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.id,
            'is_treatment_invoice': True,
            'invoice_origin': self.appointment_no or '',
            'invoice_line_ids': line_vals,
        })
        self.invoice_ids = [(4, invoice.id)]
        prescriptions.write({
            'state': 'invoiced',
            'treatment_invoice_id': invoice.id,
            'prescription_invoice_id': invoice.id,
        })
        return invoice

    def _action_open_invoice(self, invoice):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_invoice(self):
        self.ensure_one()
        return self._action_open_invoice(self._create_visit_invoice())

    def action_view_invoices(self):
        self.ensure_one()
        if self.invoice_count == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': self.invoice_ids[0].id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'target': 'current',
        }

    def _get_dental_service_product(self):
        """Return (or create) a generic service product used as the line product
        for dental appointment invoices. The real description comes from the
        treatment name so the product is just a carrier for the income account.

        company_id guard: 'in' [company, False] matches company-specific OR
        shared products; prevents 'Incompatible companies' crash on multi-company
        setups where an unfiltered search could return another company's product.
        """
        product = self.env['product.product'].search(
            [
                ('name', '=', 'Dental Service'),
                ('type', '=', 'service'),
                ('company_id', 'in', [self.env.company.id, False]),
            ],
            limit=1,
        )
        if not product:
            product = self.env['product.product'].create({
                'name': 'Dental Service',
                'type': 'service',
                'sale_ok': True,
                'purchase_ok': False,
                'company_id': False,  # shared across companies
                # Dental services are tax-exempt in the clinics we target;
                # a clinic that must charge VAT sets it on this product.
                'taxes_id': [(5, 0, 0)],
            })
        return product
