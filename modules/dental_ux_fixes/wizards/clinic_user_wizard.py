# -*- coding: utf-8 -*-
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
    """
    _name = 'clinic.user.wizard'
    _description = 'Create Clinic Staff User'

    name = fields.Char(string='Full Name', required=True)
    login = fields.Char(
        string='Email / Username', required=True,
        help='Used as the login and, if an invitation is sent, the address it is sent to.'
    )
    role = fields.Selection([
        ('admin', 'Clinic Administrator'),
        ('dentist', 'Clinic Dentist'),
        ('hygienist', 'Clinic Hygienist'),
        ('receptionist', 'Clinic Receptionist'),
    ], string='Role', required=True, default='receptionist')
    employee_id = fields.Many2one(
        'hr.employee', string='Link to Employee Record',
        help='Optional: attach this login to an existing employee/dentist record.'
    )
    send_invite = fields.Boolean(
        string='Send invitation email', default=True,
        help="If enabled, the new staff member receives an email to set their own password. "
             "If disabled, you will need to set a password for them manually afterwards."
    )

    _ROLE_GROUP_XMLID = {
        'admin': 'clinic_core.group_clinic_admin',
        'dentist': 'clinic_core.group_clinic_dentist',
        'hygienist': 'dental_clinical_permissions.group_clinic_hygienist',
        'receptionist': 'clinic_core.group_clinic_receptionist',
    }

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.name = self.employee_id.name
            if self.employee_id.work_email:
                self.login = self.employee_id.work_email

    def action_create_user(self):
        self.ensure_one()

        if not self.login or '@' not in self.login:
            raise UserError(_('Please enter a valid email address for the login.'))

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
