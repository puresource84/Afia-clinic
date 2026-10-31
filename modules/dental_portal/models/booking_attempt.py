from datetime import timedelta

from odoo import fields, models


class DentalBookingAttempt(models.Model):
    """Lightweight, DB-backed record of public booking-form submissions,
    used to rate-limit the unauthenticated /dental/book/submit endpoint.
    No external service or API key required (no reCAPTCHA)."""
    _name = 'dental.booking.attempt'
    _description = 'Public Booking Attempt (rate-limit log)'
    _order = 'create_date desc'

    ip_address = fields.Char(required=True, index=True)
    was_spam = fields.Boolean(
        default=False, help="True if the honeypot field was filled in.")

    _RATE_LIMIT_WINDOW_MINUTES = 10
    _RATE_LIMIT_MAX_ATTEMPTS = 5

    def _is_rate_limited(self, ip_address):
        """Return True if this IP has already made
        _RATE_LIMIT_MAX_ATTEMPTS or more submissions in the last
        _RATE_LIMIT_WINDOW_MINUTES minutes."""
        since = fields.Datetime.now() - timedelta(
            minutes=self._RATE_LIMIT_WINDOW_MINUTES)
        count = self.sudo().search_count([
            ('ip_address', '=', ip_address),
            ('create_date', '>=', since),
        ])
        return count >= self._RATE_LIMIT_MAX_ATTEMPTS

    def _log_attempt(self, ip_address, was_spam=False):
        return self.sudo().create({
            'ip_address': ip_address,
            'was_spam': was_spam,
        })
