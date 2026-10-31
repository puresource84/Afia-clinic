# -*- coding: utf-8 -*-
"""Expose the dental-specific hr.employee fields on the restricted
hr.employee.public model (the SQL-view mirror Odoo uses for avatar/mini
-profile cards shown to internal users who don't have HR access).

Root cause of the reported Access Error: 'job_position', 'specialised_in_id',
'dob', 'doctor_age', 'sex', 'is_dentist', 'reg_no' (added to hr.employee by
afia_dental_core) and 'commission_pct' (added by dental_ux_fixes) only exist
on the full hr.employee model. hr.employee.public's column list is built at
init() time purely from its own Python _fields registry (see
odoo/addons/hr/models/hr_employee_public.py:_get_fields), so any widget that
reads an employee "public profile" card (e.g. the assigned-dentist avatar
popover) for a user without hr.group_hr_user fails atomically the moment ANY
of these fields is requested and missing from that registry.

Fix: redeclare the 7 professional/clinical fields here so they're mirrored
into the public view for every internal user.

commission_pct (added to hr.employee by dental_ux_fixes) is deliberately
NOT mirrored here — it's staff compensation data, not something a
receptionist or hygienist should see on a profile popover, and mirroring
it would force this module to depend on dental_ux_fixes for column-creation
ordering, which would create a circular dependency (dental_ux_fixes already
depends on dental_soap_notes, which depends on this module). Keeping it out
avoids the cycle entirely and matches the original intent anyway.
"""
from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    job_position = fields.Char(readonly=True)
    specialised_in_id = fields.Many2one('dental.specialist', string='Specialisation', readonly=True)
    dob = fields.Date(string='Date of Birth', readonly=True)
    doctor_age = fields.Integer(readonly=True)
    sex = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], readonly=True)
    is_dentist = fields.Boolean(readonly=True)
    reg_no = fields.Char(string='Registration No.', readonly=True)
