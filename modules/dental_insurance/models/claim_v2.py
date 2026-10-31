from odoo import api, fields, models
from odoo.exceptions import UserError


class DentalInsurerV2(models.Model):
    _inherit = 'dental.insurer'

    requires_pre_auth = fields.Boolean(
        string='Requires Pre-Authorisation', default=False,
        help='Claims for this payer must be pre-authorised (with supporting '
             'documents) before approval.')
    claim_template_body = fields.Html(
        string='Claim Form Template Text',
        help='Payer-specific header/instructions printed at the top of the '
             'claim form (e.g. required declarations, submission address).')


class DentalClaimV2(models.Model):
    _inherit = 'dental.claim'

    pre_auth_attachment_ids = fields.Many2many(
        'ir.attachment', 'dental_claim_preauth_attachment_rel',
        'claim_id', 'attachment_id',
        string='Pre-Auth Documents',
        help='Supporting documents for pre-authorisation: X-rays, treatment '
             'plan, cost estimate.')
    pre_auth_no = fields.Char(string='Pre-Auth Reference', copy=False,
                              tracking=True)
    pre_auth_date = fields.Date(string='Pre-Auth Date', copy=False)
    requires_pre_auth = fields.Boolean(
        related='insurer_id.requires_pre_auth', string='Payer Needs Pre-Auth')

    def action_pre_auth(self):
        for claim in self:
            if not claim.pre_auth_attachment_ids:
                raise UserError(
                    'Attach at least one supporting document (X-ray, '
                    'treatment plan, estimate) before marking the claim '
                    'Pre-Authorised.')
            if not claim.pre_auth_no:
                raise UserError(
                    'Enter the Pre-Auth Reference issued by %s.'
                    % (claim.insurer_id.name or 'the payer'))
        res = super().action_pre_auth()
        self.filtered(lambda c: not c.pre_auth_date).write({
            'pre_auth_date': fields.Date.context_today(self)})
        return res

    def action_approve(self):
        for claim in self:
            if claim.requires_pre_auth and claim.state != 'pre_auth':
                raise UserError(
                    '%s requires pre-authorisation before approval. '
                    'Use Pre-Authorise first (with supporting documents).'
                    % claim.insurer_id.name)
        return super().action_approve()
