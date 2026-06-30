from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import http
from odoo.http import request


class DentalPatientPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if 'appointment_count' in counters:
            values['appointment_count'] = request.env['dental.appointment'].search_count(
                [('patient_id', '=', partner.id)])
        if 'prescription_count' in counters:
            values['prescription_count'] = request.env['dental.prescription'].search_count(
                [('patient_id', '=', partner.id)])
        return values

    @http.route('/my/appointments', type='http', auth='user', website=True)
    def portal_appointments(self, **kwargs):
        partner = request.env.user.partner_id
        appointments = request.env['dental.appointment'].search(
            [('patient_id', '=', partner.id)], order='appointment_date desc')
        return request.render('dental_patient_portal.portal_my_appointments', {
            'appointments': appointments,
            'page_name': 'appointment',
        })

    @http.route('/my/prescriptions', type='http', auth='user', website=True)
    def portal_prescriptions(self, **kwargs):
        partner = request.env.user.partner_id
        prescriptions = request.env['dental.prescription'].search(
            [('patient_id', '=', partner.id)], order='create_date desc')
        return request.render('dental_patient_portal.portal_my_prescriptions', {
            'prescriptions': prescriptions,
            'page_name': 'prescription',
        })