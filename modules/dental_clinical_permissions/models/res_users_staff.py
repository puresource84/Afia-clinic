# -*- coding: utf-8 -*-
"""2026-08-21, per Manhel: the Afia Clinic app can create 4 different staff
roles (Administrator, Dentist, Hygienist, Receptionist) via the Add Staff
User wizard, but there was nowhere in the app to see the resulting list of
staff/users at a glance — only the "Dentists" menu (afia_dental_core's
dental_staff, action view_employee_list_dentists), which only shows
hr.employee records flagged is_dentist, not clinic logins of any role.

This adds a plain, readonly "Role" label on res.users so the new Staff
list view (res_users_staff_views.xml) can show at a glance which of the 4
clinic roles each login belongs to, without duplicating the
_ROLE_GROUP_XMLID mapping already used by clinic_user_wizard.py.
"""
from odoo import api, fields, models

# Ordered so that if a user somehow belongs to more than one clinic role
# group, the highest-privilege one wins for display purposes. Kept in sync
# with clinic_user_wizard.py::_ROLE_GROUP_XMLID by hand — small, stable list.
_ROLE_LABELS = [
    ('afia_dental_core.group_clinic_admin', 'Administrator'),
    ('afia_dental_core.group_clinic_dentist', 'Dentist'),
    ('afia_dental_core.group_clinic_hygienist', 'Hygienist'),
    ('afia_dental_core.group_clinic_receptionist', 'Receptionist'),
]


class ResUsersClinicRole(models.Model):
    _inherit = 'res.users'

    clinic_role_label = fields.Char(
        string='Clinic Role', compute='_compute_clinic_role_label',
        help='Which of the 4 Afia Clinic staff roles this login belongs to, '
             'for display on the Staff list. Not stored — computed live from '
             'group membership, same groups the Add Staff User wizard assigns.'
    )

    @api.depends('groups_id')
    def _compute_clinic_role_label(self):
        role_groups = []
        for xmlid, label in _ROLE_LABELS:
            group = self.env.ref(xmlid, raise_if_not_found=False)
            role_groups.append((group, label))
        for user in self:
            label = False
            for group, group_label in role_groups:
                if group and group in user.groups_id:
                    label = group_label
                    break
            user.clinic_role_label = label

    @api.model
    def _clinic_staff_domain(self):
        """Users belonging to any of the 4 Afia Clinic staff role groups —
        i.e. anyone onboarded through the Add Staff User wizard, regardless
        of role. Used by action_clinic_staff_list's domain.
        """
        group_ids = []
        for xmlid, _label in _ROLE_LABELS:
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group:
                group_ids.append(group.id)
        return [('groups_id', 'in', group_ids)] if group_ids else [('id', '=', 0)]
