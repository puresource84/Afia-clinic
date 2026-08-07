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

    def action_create_invoice(self):
        self.ensure_one()
        if self.state != 'done':
            raise UserError(_('You can only invoice a completed appointment.'))
        if not self.treatments:
            raise UserError(_('No treatments are linked to this appointment.'))

        product = self._get_dental_service_product()

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.id,
            'is_treatment_invoice': True,
            'invoice_origin': self.appointment_no or '',
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'name': treatment.name,
                    'quantity': 1.0,
                    'price_unit': treatment.cost,
                })
                for treatment in self.treatments
            ],
        })
        self.invoice_ids = [(4, invoice.id)]

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

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
            })
        return product
