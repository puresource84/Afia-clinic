from odoo import http
from odoo.http import request


class DentalBookingController(http.Controller):

    @http.route('/dental/book', type='http', auth='public', website=True)
    def booking_page(self, **kwargs):
        dentists = request.env['hr.employee'].sudo().search(
            [('is_dentist', '=', True)])
        return request.render('dental_portal_booking.booking_page', {
            'dentists': dentists,
            'error': kwargs.get('error', ''),
        })

    @http.route('/dental/book/submit', type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def booking_submit(self, patient_name=None, patient_mobile=None,
                       dentist_id=None, appointment_date=None,
                       patient_notes=None, **kwargs):
        if not patient_name or not appointment_date:
            dentists = request.env['hr.employee'].sudo().search(
                [('is_dentist', '=', True)])
            return request.render('dental_portal_booking.booking_page', {
                'dentists': dentists,
                'error': 'Please fill all required fields.',
            })
        partner = request.env['res.partner'].sudo().search(
            [('name', '=', patient_name), ('mobile', '=', patient_mobile)], limit=1)
        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': patient_name,
                'mobile': patient_mobile or '',
                'is_patient': True,
            })
        vals = {
            'patient_id': partner.id,
            'appointment_date': appointment_date,
            'booking_source': 'online',
            'patient_notes': patient_notes or '',
        }
        if dentist_id:
            try:
                vals['dentist_id'] = int(dentist_id)
            except (ValueError, TypeError):
                pass
        request.env['dental.appointment'].sudo().create(vals)
        return request.render('dental_portal_booking.booking_success', {})