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
        # Go through the real workflow so everything hooked on action_done
        # runs (consumable stock deduction, recall dates, end-time stamp).
        for apt in self:
            if apt.state == 'draft':
                apt.action_confirm()
            apt.action_done()

    def action_flow_paid(self):
        """Take payment at the desk: post the visit invoice if needed and
        open the standard Register Payment dialog on the cash journal. The
        card only moves to Paid once the invoice is actually paid."""
        self.ensure_one()
        invoice = self._get_active_invoices()[:1] or self._create_visit_invoice()
        if invoice.state == 'draft':
            invoice.action_post()
        if invoice.payment_state in ('paid', 'in_payment', 'reversed'):
            self._set_flow_state('paid')
            return True
        action = invoice.action_register_payment()
        cash_journal = self.env['account.journal'].search([
            *self.env['account.journal']._check_company_domain(invoice.company_id),
            ('type', '=', 'cash'),
        ], limit=1)
        if cash_journal:
            action['context'] = dict(action.get('context') or {},
                                     default_journal_id=cash_journal.id)
        return action

    def _sync_flow_paid_from_invoices(self):
        for apt in self:
            invoices = apt._get_active_invoices().filtered(
                lambda m: m.state == 'posted')
            if (apt.flow_state == 'done' and invoices and all(
                    m.payment_state in ('paid', 'in_payment')
                    for m in invoices)):
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
        invoice = self._get_active_invoices()[:1]
        if not invoice:
            invoice = self._create_visit_invoice()
            invoice.action_post()
        return self._action_open_invoice(invoice)
