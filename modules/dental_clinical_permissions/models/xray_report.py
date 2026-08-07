# -*- coding: utf-8 -*-
"""Replace hard delete with soft delete (archive) on X-Ray Reports, and add a
chatter audit trail — per Manhel's 2026-07-24 instruction that any model with
a delete capability should (a) prefer archiving over permanent deletion so
imaging/clinical data is never lost, and (b) log who changed what via the
standard Odoo chatter rather than a silent, untracked action.

We deliberately do NOT grant perm_unlink=1 to any group on xray.report
(afia_dental_core.access_xray_report keeps unlink=False for everyone, and no
new ir.model.access row grants it either). Adding `active` here is what
makes the standard "Archive" action available in the list/form Action menu —
Odoo shows it automatically once a model has an `active` field, no view
changes needed for that part. Archiving only needs perm_write, which
Clinician-level groups already have.
"""
from odoo import fields, models


class XRayReport(models.Model):
    _name = 'xray.report'
    _inherit = ['xray.report', 'mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True, tracking=True)
