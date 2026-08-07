from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Mapping: appointment.state -> default flow_state when a state transition occurs.
_STATE_TO_FLOW = {
    'confirmed': 'expected',
    'in_progress': 'in_chair',
    'done': 'done',
    'cancelled': 'cancelled',
}


class DentalAppointmentFlow(models.Model):
    _inherit = 'dental.appointment'

    flow_state = fields.Selection([
        ('expected',   'Expected'),
        ('arrived',    'Arrived'),
        ('in_chair',   'In Chair'),
        ('done',       'Done'),
        ('paid',       'Paid'),
        ('cancelled',  'Cancelled'),
    ], string='Visit Stage', default='expected', tracking=True, index=True,
        copy=False,
        group_expand='_group_expand_flow_state',
        help='Day-of visit stage for the front-desk flow board.')

    flow_state_changed_at = fields.Datetime(
        string='Stage Changed At', readonly=True, copy=False)

    wait_minutes = fields.Integer(
        string='Wait (min)', compute='_compute_wait_minutes')

    cancellation_reason = fields.Text(
        string='Cancellation Reason', copy=False)

    # Stub field so the kanban view validates while this module loads.
    # dental_ux_fixes (which depends on this module and loads after it)
    # re-defines invoice_count with the real Many2many-based compute.
    invoice_count = fields.Integer(
        string='Invoices',
        compute='_compute_invoice_count_stub',
        store=False,
    )

    @api.model
    def _group_expand_flow_state(self, states, domain):
        return [key for key, _label in self._fields['flow_state'].selection]

    @api.depends('flow_state_changed_at')
    def _compute_wait_minutes(self):
        now = fields.Datetime.now()
        for apt in self:
            if apt.flow_state_changed_at and apt.flow_state in ('arrived', 'in_chair'):
                delta = now - apt.flow_state_changed_at
                apt.wait_minutes = int(delta.total_seconds() // 60)
            else:
                apt.wait_minutes = 0

    def _compute_invoice_count_stub(self):
        # Placeholder — dental_ux_fixes overrides invoice_count with the
        # real compute once it loads.  This stub prevents a view-validation
        # ParseError when dental_patient_flow loads before dental_ux_fixes.
        for apt in self:
            apt.invoice_count = 0

    def write(self, vals):
        result = super().write(vals)
        if 'state' in vals:
            flow = _STATE_TO_FLOW.get(vals['state'])
            if flow == 'cancelled':
                # Any path that cancels the appointment (core's own Cancel
                # button, the Patient Flow wizard, or an automation like the
                # Telegram bot) must also move flow_state to 'cancelled' —
                # the front-desk board groups/filters by flow_state, so
                # leaving it stuck at the prior stage hides a cancelled
                # appointment from the Cancelled column and keeps it
                # visible (and actionable) in its old one.
                for apt in self:
                    if apt.flow_state != 'cancelled':
                        apt._set_flow_state('cancelled')
            elif flow:
                _order = ['expected', 'arrived', 'in_chair', 'done', 'paid']
                for apt in self:
                    current_idx = _order.index(apt.flow_state) if apt.flow_state in _order else -1
                    new_idx = _order.index(flow) if flow in _order else -1
                    if new_idx > current_idx:
                        apt._set_flow_state(flow)
        return result

    def _set_flow_state(self, new_state):
        self.write({
            'flow_state': new_state,
            'flow_state_changed_at': fields.Datetime.now(),
        })

    def action_flow_arrived(self):
        for apt in self:
            apt._set_flow_state('arrived')

    def action_flow_in_chair(self):
        for apt in self:
            apt._set_flow_state('in_chair')

    def action_flow_done(self):
        for apt in self:
            apt._set_flow_state('done')

    def action_flow_paid(self):
        for apt in self:
            apt._set_flow_state('paid')

    def action_request_cancel(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Appointment',
            'res_model': 'appointment.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_appointment_id': self.id},
        }

    def action_flow_invoice(self):
        self.ensure_one()
        if self.invoice_count:
            return self.action_view_invoices()
        if not self.treatments:
            raise UserError(
                _('No treatments linked to appointment %s. Add treatments before invoicing.')
                % (self.appointment_no or self.id)
            )
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
