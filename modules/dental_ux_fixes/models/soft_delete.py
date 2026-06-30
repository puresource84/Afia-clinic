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
        """Archive instead of permanently deleting to preserve history."""
        self.write({'active': False})
        return True
