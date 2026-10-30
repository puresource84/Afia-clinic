from odoo import api, models


class ResPartnerPatientSearch(models.Model):
    _inherit = 'res.partner'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """QA fix: make patient-number lookup actually work.

        2026-09-20 (afia_dental_core-name-search-stale-docstring, system
        audit Domain D2): the paragraph below described a BUG in
        afia_dental_core.name_search that was already fixed on
        2026-08-26 (see afia_dental_core/models/res_partner.py — it now
        does its own combined `name OR patient_no` search and no longer
        forwards to super() when `name` is truthy). This docstring was
        stale and described pre-fix behavior — corrected here so it
        doesn't mislead whoever reads it next while debugging a real
        search issue.

        Original note (now historical/inaccurate as of 2026-08-26, kept
        for context): "afia_dental_core.name_search already tries this,
        but it appends the patient_no condition to the domain AND still
        forwards `name` to super(), which ANDs an unmatchable
        display-name filter on top and returns nothing."

        Current behavior / why this override still exists: this resolves
        an EXACT/prefix patient_no match first, on its own (not OR'd with
        a name match), before falling through via super() to
        afia_dental_core's combined `name OR patient_no` search. In
        practice these return the same results for a typical numeric
        patient_no format (no overlap with name substrings), so this is
        redundant with — not a fix for — the current afia_dental_core
        implementation. Deliberately NOT removed in this pass despite the
        redundancy: doing so would change matching behavior in the
        (rare, format-dependent) case where a patient_no could also
        overlap a name substring, which is a decision for Manhel, not an
        unattended cleanup. See the audit doc for the removal option.
        """
        if name and operator in ('ilike', 'like', '=ilike', '=like', '='):
            ids = self._search(
                [('patient_no', operator, name)] + (args or []),
                limit=limit)
            if ids:
                return [(rec.id, rec.display_name)
                        for rec in self.browse(ids)]
        return super().name_search(name, args, operator, limit)
