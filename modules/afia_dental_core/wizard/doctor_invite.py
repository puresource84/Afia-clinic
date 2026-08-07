# -*- coding: utf-8 -*-
"""Deliberate, auditable doctor system-access invite. Replaces the old
silent/passwordless auto-user-creation on every employee record."""
import secrets
import string

from odoo import _, api, fields, models
from odoo.exceptions import UserError


def _generate_temp_password(length=14):
    alphabet = string.ascii_letters + string.digits + '!@#$%'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class DentalDoctorInvite(models.TransientModel):
    _name = 'dental.doctor.invite'
    _description = 'Grant Doctor System Access'

    employee_id = fields.Many2one('hr.employee', required=True)
    login = fields.Char(
        string='Login', required=True,
        help='Email is preferred. Falls back to mobile number if the '
             'clinic has no mail server configured yet.')
    group_ids = fields.Many2many(
        'res.groups', string='Access Groups',
        default=lambda self: self.env.ref(
            'afia_dental_core.group_dental_dentist', raise_if_not_found=False))
    temp_password = fields.Char(readonly=True, copy=False)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        employee = self.env['hr.employee'].browse(res.get('employee_id'))
        if employee:
            res['login'] = employee.work_email or employee.mobile_phone or ''
        return res

    def action_grant_access(self):
        self.ensure_one()
        if not self.login:
            raise UserError(_('Provide an email or mobile number to use as the login.'))
        if self.env['res.users'].sudo().search_count([('login', '=', self.login)]):
            raise UserError(_('A user with this login already exists.'))

        temp_password = _generate_temp_password()
        user = self.env['res.users'].sudo().create({
            'name': self.employee_id.name,
            'login': self.login,
            'password': temp_password,
            'employee_id': self.employee_id.id,
            'company_id': self.employee_id.company_id.id,
            'group_ids': [(6, 0, self.group_ids.ids)],
        })
        self.employee_id.user_id = user.id
        self.employee_id.message_post(body=_(
            'System access granted (login: %(login)s). Ask the doctor to '
            'change the temporary password on first login.', login=self.login))

        # Prefer Odoo's normal signup/reset-password email if outgoing
        # mail is configured; the temporary password is still shown below
        # as a fallback for clinics without SMTP set up yet.
        try:
            user.action_reset_password()
        except Exception:
            pass

        self.write({'temp_password': temp_password, 'state': 'done'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dental.doctor.invite',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
