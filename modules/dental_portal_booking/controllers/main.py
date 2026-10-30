import logging

from odoo import _, fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


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

    def _antispam_guard(self, website):
        """Honeypot + per-IP rate limit, shared by every booking path.
        Returns a response to send back when the request must stop, else None.

        1) honeypot - a field named "website" hidden off-screen in the
           template. Real visitors never fill it; bots that auto-fill every
           input do. Pretend success so the bot learns nothing.
        2) simple IP-based rate limit - max 5 submissions per 10 minutes.
        """
        ip = request.httprequest.remote_addr or 'unknown'
        attempt_model = request.env['dental.booking.attempt']
        if website:
            attempt_model._log_attempt(ip, was_spam=True)
            return request.render('dental_portal_booking.booking_success', {})
        if attempt_model._is_rate_limited(ip):
            return self._render_error(
                _('Too many booking requests from this connection. '
                  'Please try again later or call the clinic directly.'))
        attempt_model._log_attempt(ip)
        return None

    def _find_or_create_patient(self, name, mobile):
        """Reuse an existing patient only when name AND a mobile number
        match; without a mobile, a same-name stranger must never be
        attached to someone else's record."""
        Partner = request.env['res.partner'].sudo()
        partner = Partner.browse()
        if mobile:
            partner = Partner.search(
                [('name', '=', name), ('mobile', '=', mobile)], limit=1)
        return partner or Partner.create({
            'name': name,
            'mobile': mobile or '',
            'is_patient': True,
        })

    @http.route('/dental/book/submit', type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def booking_submit(self, patient_name=None, patient_mobile=None,
                       dentist_id=None, appointment_date=None,
                       patient_notes=None, website=None, **kwargs):
        blocked = self._antispam_guard(website)
        if blocked:
            return blocked

        if not patient_name or not appointment_date:
            return self._render_error(_('Please fill all required fields.'))
        try:
            date_val = fields.Date.to_date(appointment_date)
        except (TypeError, ValueError):
            date_val = None
        if not date_val:
            return self._render_error(_('Invalid appointment date.'))

        Appointment = request.env['dental.appointment'].sudo()
        candidates = request.env['hr.employee'].sudo().search(
            [('is_dentist', '=', True)])
        if dentist_id:
            try:
                candidates = candidates.filtered(lambda d: d.id == int(dentist_id))
            except (ValueError, TypeError):
                pass
        if not candidates:
            return self._render_error(
                _('No dentists are currently available for online booking. '
                  'Please call the clinic.'))
        # Date-only form: book the earliest free slot that day (respecting
        # shifts, existing appointments, leaves and holidays) instead of
        # stamping the booking with the current time of day.
        chosen = None
        for dentist in candidates:
            free = Appointment.get_available_slots(dentist.id, date_val)
            if free:
                chosen = (dentist, free[0])
                break
        if not chosen:
            return self._render_error(
                _('Sorry, there is no free time on that day. Please pick '
                  'another date or call the clinic.'))
        dentist, slot = chosen
        partner = self._find_or_create_patient(patient_name, patient_mobile)
        vals = {
            'patient_id': partner.id,
            'dentist_id': dentist.id,
            'start_datetime': Appointment._local_to_utc(date_val, slot),
            'booking_source': 'online',
            'patient_notes': patient_notes or '',
        }
        try:
            Appointment.create(vals)
        except Exception:
            # Never expose a traceback on the public site, but log it.
            _logger.exception(
                'dental_portal_booking: booking_submit failed for %s '
                '(mobile %s, date %s). vals=%r',
                patient_name, patient_mobile, appointment_date, vals)
            return self._render_error(
                _('We could not register your booking. Please call the clinic '
                  'or try again later.'))
        return request.render('dental_portal_booking.booking_success', {})
