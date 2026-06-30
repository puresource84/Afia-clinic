import json
from datetime import datetime

from odoo import http
from odoo.http import request

from odoo.addons.dental_portal_booking.controllers.main import (
    DentalBookingController,
)


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
                       slot_dentist=None, **kwargs):
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
                patient_notes=patient_notes, **kwargs)

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

        partner = request.env['res.partner'].sudo().search(
            [('name', '=', patient_name),
             ('mobile', '=', patient_mobile)], limit=1)
        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': patient_name,
                'mobile': patient_mobile or '',
                'is_patient': True,
            })
        shift = Appointment._shift_for_slot(final_dentist, slot)
        try:
            Appointment.create({
                'patient_id': partner.id,
                'appointment_date': appointment_date,
                'dentist_id': final_dentist,
                'shift_id': shift.id or False,
                'booking_slot': slot,
                'booking_source': 'online',
                'patient_notes': patient_notes or '',
            })
        except Exception:
            return self._render_error(
                'We could not register your booking. Please call the clinic '
                'or try again later.')
        return request.render('dental_portal_booking.booking_success', {})
