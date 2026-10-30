from odoo import fields, models


class DentalAppointmentArchive(models.Model):
    """Soft-delete support: archive appointments instead of hard-deleting.

    Adding ``active`` on dental.appointment means the ORM automatically
    excludes archived records from normal searches (active_test=True).
    Staff can recover them via the "Archived" filter on the list view.
    """
    _inherit = 'dental.appointment'

    active = fields.Boolean(
        default=True,
        help='Uncheck to archive this appointment. Archived appointments are '
             'hidden from normal views but kept in the database for audit.',
    )

    def unlink(self):
        """Archive instead of permanently deleting, to preserve the clinical
        record for audit.

        The linked calendar event must still be deactivated. This override
        replaces dental_appointment.unlink(), which deleted the event, so
        without this the slot stayed booked on the dentist's calendar and a
        deleted appointment showed up as a ghost booking. Deactivating rather
        than deleting matches action_cancel().
        """
        self.calendar_event_id.write({'active': False})
        self.write({'active': False})
        return True
