from odoo import api, models


def _fmt(value):
    """8.5 -> '08:30'"""
    hours = int(value)
    minutes = int(round((value - hours) * 60))
    return '%02d:%02d' % (hours, minutes)


class DentalTimeShiftFixes(models.Model):
    _inherit = 'dental.time.shift'

    def _shift_label(self, start, end):
        return '%s - %s' % (_fmt(start or 0.0), _fmt(end or 0.0))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.name = self._shift_label(rec.start_time, rec.end_time)
        return records

    @api.onchange('start_time', 'end_time')
    def _onchange_time(self):
        self.update({'name': self._shift_label(self.start_time, self.end_time)})

    def init(self):
        """One-time cleanup: reformat legacy float-style names (e.g. '8.0 to 14.0')."""
        legacy = self.search([('name', 'like', '%to%')])
        for rec in legacy:
            rec.name = self._shift_label(rec.start_time, rec.end_time)
