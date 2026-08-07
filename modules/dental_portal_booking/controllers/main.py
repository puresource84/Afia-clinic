from odoo import _, http
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

    def _render_error(self, message):
        dentists = request.env['hr.employee'].sudo().search(
            [('is_dentist', '=', True)])
        return request.render('dental_portal_booking.booking_page', {
            'dentists': dentists,
            'error': message,
        })

    @http.route('/dental/book/submit', type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def booking_submit(self, patient_name=None, patient_mobile=None,
                       dentist_id=None, appointment_date=None,
                       patient_notes=None, website=None, **kwargs):
        # Anti-spam, no external service/registration required:
        # 1) honeypot — a field named "website" that is hidden off-screen in
        #    the template. Real visitors never see or fill it; bots that
        #    auto-fill every input on the page do. If it's non-empty, log it
        #    as spam and pretend the booking succeeded (don't tip off the bot).
        ip = request.httprequest.remote_addr or 'unknown'
        attempt_model = request.env['dental.booking.attempt']
        if website:
            attempt_model._log_attempt(ip, was_spam=True)
            return request.render('dental_portal_booking.booking_success', {})
        # 2) simple IP-based rate limit — max 5 submissions per 10 minutes.
        if attempt_model._is_rate_limited(ip):
            return self._render_error(
                _('Too many booking requests from this connection. '
                  'Please try again later or call the clinic directly.'))
        attempt_model._log_attempt(ip)

        if not patient_name or not appointment_date:
            return self._render_error(_('Please fill all required fields.'))
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
        # QA fix 2026-06-11: dentist_id is required on dental.appointment.
        # "-- Any Available --" submissions crashed with a public traceback.
        if not vals.get('dentist_id'):
            fallback = request.env['hr.employee'].sudo().search(
                [('is_dentist', '=', True)], limit=1)
            if not fallback:
                return self._render_error(
                    _('No dentists are currently available for online booking. '
                      'Please call the clinic.'))
            vals['dentist_id'] = fallback.id
        try:
            request.env['dental.appointment'].sudo().create(vals)
        except Exception:
            # Never expose a traceback on the public site.
            return self._render_error(
                _('We could not register your booking. Please call the clinic '
                  'or try again later.'))
        return request.render('dental_portal_booking.booking_success', {})
