from odoo import api, fields, models
from odoo.exceptions import UserError


class DentalTreatmentPlanAcceptance(models.Model):
    """A8: case-acceptance workflow + B3 e-signature on treatment plans.

    Lifecycle: Draft -> Proposed (presented to patient) -> Accepted (signed)
    or Declined -> In Progress -> Completed. Acceptance rate is the #2
    revenue lever in dentistry (EXPERT_ROADMAP A8).
    """
    _inherit = 'dental.treatment.plan'

    state = fields.Selection(
        selection_add=[
            ('proposed', 'Proposed'),
            ('accepted', 'Accepted'),
            ('declined', 'Declined'),
            ('in_progress',),
        ],
        ondelete={
            'proposed': 'set default',
            'accepted': 'set default',
            'declined': 'set default',
        })

    presented_date = fields.Datetime(string='Presented On', readonly=True, copy=False)
    accepted_date = fields.Datetime(string='Accepted On', readonly=True, copy=False)
    declined_date = fields.Datetime(string='Declined On', readonly=True, copy=False)
    accepted_by = fields.Char(
        string='Accepted By (Printed Name)', copy=False,
        help='Name of the patient or guardian who signed.')
    patient_signature = fields.Binary(string='Patient Signature', copy=False)
    decline_reason = fields.Text(string='Decline Reason', copy=False)
    days_to_decision = fields.Integer(
        string='Days to Decision', compute='_compute_days_to_decision', store=True,
        help='Days between presentation and patient decision.')

    @api.depends('presented_date', 'accepted_date', 'declined_date')
    def _compute_days_to_decision(self):
        for plan in self:
            decision = plan.accepted_date or plan.declined_date
            if plan.presented_date and decision:
                plan.days_to_decision = (decision - plan.presented_date).days
            else:
                plan.days_to_decision = 0

    def action_present(self):
        for plan in self:
            if not plan.line_ids:
                raise UserError(
                    'Add at least one session before presenting the plan '
                    'to the patient.')
        self.write({'state': 'proposed', 'presented_date': fields.Datetime.now()})
        for plan in self:
            plan.message_post(body='Treatment plan presented to patient.')

    def action_accept(self):
        for plan in self:
            if not plan.patient_signature:
                raise UserError(
                    'Patient signature is required to accept the plan. '
                    'Use the signature pad in the Case Acceptance tab.')
            if not plan.accepted_by:
                raise UserError(
                    'Enter the printed name of the person signing '
                    '(Accepted By).')
        self.write({'state': 'accepted', 'accepted_date': fields.Datetime.now()})
        for plan in self:
            plan.message_post(
                body='Plan ACCEPTED — signed by %s.' % plan.accepted_by)

    def action_decline_case(self):
        self.write({'state': 'declined', 'declined_date': fields.Datetime.now()})
        for plan in self:
            plan.message_post(
                body='Plan declined.%s' % (
                    ' Reason: %s' % plan.decline_reason
                    if plan.decline_reason else ''))

    def action_reopen_proposal(self):
        """Declined plans can be re-presented (revised offer)."""
        self.write({'state': 'proposed', 'presented_date': fields.Datetime.now()})
