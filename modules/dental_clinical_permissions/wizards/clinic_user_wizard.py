# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ClinicUserWizard(models.TransientModel):
    """Create a clinic staff login (res.users) from inside the Afia Clinic
    app, with the correct Clinic role group pre-selected — so clinic staff
    never need to open Settings > Users & Companies to be onboarded.

    Only the four real, currently-used Clinic roles are offered here
    (Administrator, Dentist, Hygienist, Receptionist). The legacy "Hospital"
    groups are intentionally not exposed — see the Access Rights cleanup in
    project memory (2026-07-05).

    Five options for four groups: "Dentist (also manages the clinic)" maps to
    the same group as Clinic Administrator. In a small practice the dentist
    IS the administrator, and the role ladder already covers that case —
    group_clinic_admin implies group_clinic_dentist, so such a dentist keeps
    every clinical capability and gains configuration. It is offered as its
    own option because an owner-dentist reading "Clinic Administrator" has
    no way to know it includes treating patients, and would otherwise pick
    Dentist and then find Configuration missing.
    """
    _name = 'clinic.user.wizard'
    _description = 'Create Clinic Staff User'

    name = fields.Char(string='Full Name', required=True)
    login = fields.Char(
        string='Email / Username', required=True,
        help='Used as the login and, if an invitation is sent, the address it is sent to.'
    )
    role = fields.Selection([
        ('receptionist', 'Receptionist'),
        ('hygienist', 'Hygienist'),
        ('dentist', 'Dentist'),
        ('dentist_admin', 'Dentist (also manages the clinic)'),
        ('admin', 'Clinic Administrator'),
    ], string='Role', required=True, default='receptionist',
        help="Each role includes everything the one above it can do.\n\n"
             "Receptionist — appointments, patients, billing, lab orders.\n"
             "Hygienist — the above, plus charting and periodontal exams.\n"
             "Dentist — the above, plus prescriptions, clinical notes and "
             "treatment plans.\n"
             "Dentist (also manages the clinic) — a dentist who also gets "
             "clinic Configuration. Choose this for the owner-dentist of a "
             "small practice.\n"
             "Clinic Administrator — full access, including staff accounts "
             "and reports.")
    employee_id = fields.Many2one(
        'hr.employee', string='Link to Employee Record',
        help='Optional: attach this login to an existing employee/dentist record.'
    )
    send_invite = fields.Boolean(
        string='Send invitation email', default=True,
        help="If enabled, the new staff member receives an email to set their own password. "
             "If disabled, you will need to set a password for them manually afterwards."
    )
    capacity_info = fields.Html(
        string='Plan Capacity', readonly=True,
        help="Live dentist-seat usage against the clinic's ITCS license plan. "
             "Only shown/enforced for the Clinic Dentist role — see "
             "itcs_license_manager for what this counts."
    )

    # dentist_admin and admin deliberately share a group: see the class
    # docstring. The two options differ only in how they read to the person
    # filling in the form.
    _ROLE_GROUP_XMLID = {
        'admin': 'afia_dental_core.group_clinic_admin',
        'dentist_admin': 'afia_dental_core.group_clinic_admin',
        'dentist': 'afia_dental_core.group_clinic_dentist',
        'hygienist': 'afia_dental_core.group_clinic_hygienist',
        'receptionist': 'afia_dental_core.group_clinic_receptionist',
    }

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.name = self.employee_id.name
            if self.employee_id.work_email:
                self.login = self.employee_id.work_email

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'capacity_info' in fields_list:
            res['capacity_info'] = self._capacity_info_html(res.get('role', 'receptionist'))
        return res

    @api.onchange('role')
    def _onchange_role_capacity_info(self):
        self.capacity_info = self._capacity_info_html(self.role)

    def _capacity_info_html(self, role):
        """Live dentist-seat usage banner, shown only for the Clinic Dentist
        role since that's the only role this wizard's cap check applies to
        (the ITCS license only tracks dentist/patient capacity — see
        itcs_license_manager/models/itcs_license.py). Mirrors the wording
        style of the list-view seat banners (list_banner.js) for consistency,
        but is rendered server-side here since this is a plain form field,
        not a list view the OWL patch can hook into.
        """
        # dentist_admin is a dentist and takes a dentist seat, so the banner
        # applies to it too.
        if role not in ('dentist', 'dentist_admin'):
            return False
        # itcs_license_manager is a soft/optional dependency, not declared in
        # this module's manifest (see App Store scoping note in
        # ADD_STAFF_USER_CAPACITY.md) — this wizard must keep working when
        # that module isn't installed (e.g. an Odoo App Store build of this
        # package), so guard the model lookup instead of assuming it exists.
        if 'itcs.license' not in self.env:
            return False
        License = self.env['itcs.license'].sudo()
        license_rec = License.get_active_license()
        if not license_rec:
            return False
        info = license_rec._afia_banner_info('dentist')
        if info['type'] == 'none':
            return False
        css_class = {
            'ok': 'alert alert-success py-1 px-2 mb-0',
            'warning': 'alert alert-warning py-1 px-2 mb-0',
            'danger': 'alert alert-danger py-1 px-2 mb-0',
        }.get(info['type'], 'alert alert-secondary py-1 px-2 mb-0')
        return Markup('<div class="%s"><strong>%s</strong></div>') % (
            css_class, info['text']
        )

    def action_create_user(self):
        self.ensure_one()

        if not self.login or '@' not in self.login:
            raise UserError(_('Please enter a valid email address for the login.'))

        # Enforce the clinic's dentist-seat plan cap when onboarding a new
        # Clinic Dentist login. The ITCS license only counts hr.employee
        # records flagged is_dentist=True (see itcs_license_manager), which
        # this wizard does not create/flag on its own — so this check treats
        # "one more Clinic Dentist login about to be created" as +1 against
        # the current active_dentist_count as a deliberate, slightly
        # conservative proxy for "onboarding a new dentist," rather than
        # waiting for a separate hr.employee edit to trip the cap later.
        # 2026-08-21, per Manhel: enforced version of the wizard-level
        # capacity check, see dental_ux_fixes/ADD_STAFF_USER_CAPACITY.md.
        # Same optional-dependency guard as _capacity_info_html() above —
        # skip the cap check entirely (not just fail open, but not error)
        # when itcs_license_manager isn't installed.
        if self.role in ('dentist', 'dentist_admin') and 'itcs.license' in self.env:
            license_rec = self.env['itcs.license'].sudo().get_active_license()
            if license_rec:
                license_rec._afia_check_cap('dentist', license_rec.active_dentist_count + 1)

        existing = self.env['res.users'].sudo().search([('login', '=', self.login)], limit=1)
        if existing:
            raise UserError(_('A user with the login "%s" already exists.') % self.login)

        group_xmlid = self._ROLE_GROUP_XMLID.get(self.role)
        group = self.env.ref(group_xmlid, raise_if_not_found=False)
        if not group:
            raise UserError(_(
                'Could not find the security group for role "%s" (%s). '
                'Please check with your administrator before continuing.'
            ) % (self.role, group_xmlid))

        # The Clinic role groups alone do not imply "Internal User" (base.group_user).
        # Without it explicitly, Odoo treats the new account as an external/portal
        # user (share=True) instead of full clinic staff — always include it.
        internal_user_group = self.env.ref('base.group_user')

        vals = {
            'name': self.name,
            'login': self.login,
            'email': self.login,
            'groups_id': [(6, 0, [group.id, internal_user_group.id])],
        }
        if self.employee_id:
            vals['employee_ids'] = [(4, self.employee_id.id)]

        new_user = self.env['res.users'].with_context(
            no_reset_password=not self.send_invite
        ).create(vals)

        if self.send_invite:
            new_user.action_reset_password()

        message = _('Staff account created for %s.') % self.name
        if self.send_invite:
            message += _(' An invitation email has been sent to %s.') % self.login
        else:
            message += _(' No invitation was sent — set a password for them manually.')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('User Created'),
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
