from odoo import api, models


class ResPartnerPatientSearch(models.Model):
    _inherit = 'res.partner'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """QA fix: make patient-number lookup actually work.

        dental_hospital.name_search already tries this, but it appends the
        patient_no condition to the domain AND still forwards `name` to
        super(), which ANDs an unmatchable display-name filter on top and
        returns nothing. Here we resolve patient_no matches first, ourselves,
        and only fall back to the standard chain when there is none.
        """
        if name and operator in ('ilike', 'like', '=ilike', '=like', '='):
            ids = self._search(
                [('patient_no', operator, name)] + (args or []),
                limit=limit)
            if ids:
                return [(rec.id, rec.display_name)
                        for rec in self.browse(ids)]
        return super().name_search(name, args, operator, limit)
