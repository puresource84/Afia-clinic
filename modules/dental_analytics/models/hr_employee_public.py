# -*- coding: utf-8 -*-
"""Mirror commission_pct onto hr.employee.public.

hr.employee.public is the restricted SQL-view mirror Odoo serves to internal
users without HR access. Odoo's hr.employee read override refuses the whole
read if ANY requested field is missing from that model, so a single unmirrored
field breaks every screen that touches an employee for those users - here, the
appointment calendar, which left a receptionist unable to open the clinic at
all.

dental_clinical_permissions already mirrors seven other dental fields for this
reason and deliberately left this one out, because at the time commission_pct
was added by dental_ux_fixes and mirroring it would have created a circular
dependency. dental_ux_fixes no longer exists and the field is defined in this
module, so the mirror belongs here, next to the field it mirrors.

The privacy concern that motivated leaving it out still stands, and is handled
properly: the field-level `groups` means a receptionist or hygienist cannot
read the value. It exists on the model so the read succeeds; it stays empty
for anyone who should not see staff compensation.
"""
from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    commission_pct = fields.Float(
        string='Commission %', readonly=True,
        groups='base.group_system,afia_dental_core.group_clinic_admin',
    )
