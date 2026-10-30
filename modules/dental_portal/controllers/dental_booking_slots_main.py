import json
import logging
from datetime import datetime

from odoo import http
from odoo.http import request

# DentalBookingController moved to dental_portal_booking_main.py when the
# portal modules were merged (three controllers/main.py collided).
from odoo.addons.dental_portal.controllers.dental_portal_booking_main import (
    DentalBookingController,
)

_logger = logging.getLogger(__name__)


class DentalBookingSlotsController(DentalBookingController):

    @http.route('/dental/book/slots', type='http', auth='public',
                website=True, methods=['GET'])
    def booking_slots(self, date=None, dentist_id=None, **kwargs):
        """JSON: free slots for a date (+optional dentist)."""
        try:
            date_val = datetime.strptime(date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return request.make_response(
                json.dumps({'slots': [], 'error': 'invalid date'}),
                headers=[('Content-Type', 'application/json')])
        try:
            d_id = int(dentist_id) if dentist_id else None
        except (TypeError, ValueError):
            d_id = None
        slots = request.env['dental.appointment'].sudo().get_slot_map(
            date_val, d_id)
        return request.make_response(
            json.dumps({'slots': slots}),
            headers=[('Content-Type', 'application/json')])

    @http.route('/dental/book/submit', type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def booking_submit(self, patient_name=None, patient_mobile=None,
                       dentist_id=None, appointment_date=None,
                       patient_notes=None, slot_value=None,
                       slot_dentist=None, website=None, **kwargs):
        """Slot-aware submission. Falls back to the date-only flow when no
        slot was picked (JS disabled)."""
        slot = None
        try:
            slot = float(slot_value) if slot_value else None
        except (TypeError, ValueError):
            slot = None
        if not slot:
            return super().booking_submit(
                patient_name=patient_name, patient_mobile=patient_mobile,
                dentist_id=dentist_id, appointment_date=appointment_date,
                patient_notes=patient_notes, website=website, **kwargs)

        # Same honeypot + rate limit as the date-only form (previously
        # skipped whenever a slot was picked).
        blocked = self._antispam_guard(website)
        if blocked:
            return blocked

        if not patient_name or not appointment_date:
            return self._render_error('Please fill all required fields.')
        try:
            date_val = datetime.strptime(
                appointment_date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return self._render_error('Invalid appointment date.')

        Appointment = request.env['dental.appointment'].sudo()
        # Resolve dentist: explicit choice, else the dentist the slot map
        # assigned, validated server-side either way.
        chosen = None
        for raw in (dentist_id, slot_dentist):
            try:
                if raw and int(raw):
                    chosen = int(raw)
                    break
            except (TypeError, ValueError):
                continue
        candidates = (
            [chosen] if chosen else
            request.env['hr.employee'].sudo().search(
                [('is_dentist', '=', True)]).ids)
        final_dentist = None
        for cand in candidates:
            if slot in Appointment.get_available_slots(cand, date_val):
                final_dentist = cand
                break
        if not final_dentist:
            return self._render_error(
                'Sorry, that time was just taken. Please pick another slot.')

        partner = self._find_or_create_patient(patient_name, patient_mobile)
        shift = Appointment._shift_for_slot(final_dentist, slot)
        booking_vals = {
            'patient_id': partner.id,
            'start_datetime': Appointment._local_to_utc(date_val, slot),
            'dentist_id': final_dentist,
            'shift_id': shift.id or False,
            'booking_slot': slot,
            'booking_source': 'online',
            'patient_notes': patient_notes or '',
        }
        try:
            Appointment.create(booking_vals)
        except Exception:
            # 2026-09-20 (afia_dental_core-silent-booking-failure, system
            # audit Domain C2): see dental_portal_booking's identical fix —
            # never expose a traceback publicly, but log server-side now.
            _logger.exception(
                'dental_booking_slots: booking_submit failed for %s '
                '(mobile %s, date %s). vals=%r',
                patient_name, patient_mobile, appointment_date, booking_vals)
            return self._render_error(
                'We could not register your booking. Please call the clinic '
                'or try again later.')
        return request.render('dental_portal.booking_success', {})
