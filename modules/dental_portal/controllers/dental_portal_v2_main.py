"""C4 – Dental Portal v2 controllers.

Routes added
------------
/my/treatment-plans                 – plan list
/my/treatment-plans/<id>            – plan detail (GET)
/my/treatment-plans/<id>/accept     – patient accept  (POST)
/my/treatment-plans/<id>/decline    – patient decline (POST)
/my/dental/invoices                 – dental invoice history
/my/dental/documents                – consent-form library
"""
from odoo import fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, UserError
from odoo.http import request


def _get_plan_or_403(plan_id):
    """Return the plan if it belongs to the current portal patient, else 403."""
    partner = request.env.user.partner_id
    plan = request.env['dental.treatment.plan'].sudo().browse(plan_id)
    if not plan.exists() or plan.patient_id.id != partner.id:
        raise AccessError('Access denied.')
    return plan


class DentalPortalV2(CustomerPortal):

    # ── Home page counters ────────────────────────────────────────────────────

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        Plan = request.env['dental.treatment.plan'].sudo()
        Move = request.env['account.move'].sudo()
        Consent = request.env['dental.consent.form'].sudo()

        if 'plan_count' in counters:
            values['plan_count'] = Plan.search_count(
                [('patient_id', '=', partner.id)])

        if 'dental_invoice_count' in counters:
            values['dental_invoice_count'] = Move.search_count([
                ('partner_id', '=', partner.id),
                ('is_treatment_invoice', '=', True),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
            ])

        if 'consent_count' in counters:
            values['consent_count'] = Consent.search_count(
                [('patient_id', '=', partner.id)])

        return values

    # ── Treatment plans ───────────────────────────────────────────────────────

    @http.route('/my/treatment-plans', type='http', auth='user', website=True)
    def portal_treatment_plans(self, **kwargs):
        partner = request.env.user.partner_id
        plans = request.env['dental.treatment.plan'].sudo().search(
            [('patient_id', '=', partner.id)],
            order='create_date desc',
        )
        return request.render(
            'dental_portal.portal_treatment_plans',
            {'plans': plans, 'page_name': 'treatment_plan'},
        )

    @http.route('/my/treatment-plans/<int:plan_id>', type='http', auth='user', website=True)
    def portal_plan_detail(self, plan_id, error=None, success=None, **kwargs):
        plan = _get_plan_or_403(plan_id)
        return request.render(
            'dental_portal.portal_plan_detail',
            {
                'plan': plan,
                'page_name': 'treatment_plan',
                'error': error,
                'success': success,
            },
        )

    @http.route(
        '/my/treatment-plans/<int:plan_id>/accept',
        type='http', auth='user', website=True, methods=['POST'],
    )
    def portal_plan_accept(self, plan_id, accepted_by='', **kwargs):
        plan = _get_plan_or_403(plan_id)
        accepted_by = (accepted_by or '').strip()
        if not accepted_by:
            return request.redirect(
                '/my/treatment-plans/%d?error=name_required' % plan_id)
        if plan.state != 'proposed':
            return request.redirect(
                '/my/treatment-plans/%d?error=not_proposed' % plan_id)
        plan.write({
            'state': 'accepted',
            'accepted_date': fields.Datetime.now(),
            'accepted_by': accepted_by,
        })
        plan.message_post(
            body='Plan ACCEPTED via patient portal — confirmed by %s.' % accepted_by)
        return request.redirect(
            '/my/treatment-plans/%d?success=accepted' % plan_id)

    @http.route(
        '/my/treatment-plans/<int:plan_id>/decline',
        type='http', auth='user', website=True, methods=['POST'],
    )
    def portal_plan_decline(self, plan_id, decline_reason='', **kwargs):
        plan = _get_plan_or_403(plan_id)
        if plan.state != 'proposed':
            return request.redirect(
                '/my/treatment-plans/%d?error=not_proposed' % plan_id)
        plan.write({
            'state': 'declined',
            'declined_date': fields.Datetime.now(),
            'decline_reason': decline_reason or False,
        })
        plan.message_post(
            body='Plan DECLINED via patient portal.%s' % (
                ' Reason: %s' % decline_reason if decline_reason else ''))
        return request.redirect(
            '/my/treatment-plans/%d?success=declined' % plan_id)

    # ── Dental invoices ───────────────────────────────────────────────────────

    @http.route('/my/dental/invoices', type='http', auth='user', website=True)
    def portal_dental_invoices(self, **kwargs):
        partner = request.env.user.partner_id
        invoices = request.env['account.move'].sudo().search([
            ('partner_id', '=', partner.id),
            ('is_treatment_invoice', '=', True),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ], order='invoice_date desc')
        return request.render(
            'dental_portal.portal_dental_invoices',
            {'invoices': invoices, 'page_name': 'dental_invoice'},
        )

    # ── Consent documents ─────────────────────────────────────────────────────

    @http.route('/my/dental/documents', type='http', auth='user', website=True)
    def portal_dental_documents(self, **kwargs):
        partner = request.env.user.partner_id
        consents = request.env['dental.consent.form'].sudo().search(
            [('patient_id', '=', partner.id)],
            order='create_date desc',
        )
        return request.render(
            'dental_portal.portal_dental_documents',
            {'consents': consents, 'page_name': 'dental_document'},
        )
