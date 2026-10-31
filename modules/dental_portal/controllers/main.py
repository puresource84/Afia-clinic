from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import http
from odoo.http import request

# Portal users have no ACL on dental.appointment / dental.prescription, so
# every read goes through sudo() and is scoped to the logged-in patient
# (same pattern as dental_portal_v2/controllers/main.py).


class DentalPatientPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if 'appointment_count' in counters:
            values['appointment_count'] = request.env['dental.appointment'].sudo().search_count(
                [('patient_id', '=', partner.id)])
        if 'prescription_count' in counters:
            values['prescription_count'] = request.env['dental.prescription'].sudo().search_count(
                [('patient_id', '=', partner.id)])
        return values

    @http.route('/my/appointments', type='http', auth='user', website=True)
    def portal_appointments(self, **kwargs):
        partner = request.env.user.partner_id
        appointments = request.env['dental.appointment'].sudo().search(
            [('patient_id', '=', partner.id)], order='appointment_date desc')
        return request.render('dental_portal.portal_my_appointments', {
            'appointments': appointments,
            'page_name': 'appointment',
        })

    @http.route('/my/prescriptions', type='http', auth='user', website=True)
    def portal_prescriptions(self, **kwargs):
        partner = request.env.user.partner_id
        prescriptions = request.env['dental.prescription'].sudo().search(
            [('patient_id', '=', partner.id)], order='create_date desc')
        return request.render('dental_portal.portal_my_prescriptions', {
            'prescriptions': prescriptions,
            'page_name': 'prescription',
        })
