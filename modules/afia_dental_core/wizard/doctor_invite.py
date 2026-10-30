# -*- coding: utf-8 -*-
"""Deliberate, auditable doctor system-access invite. Replaces the old
silent/passwordless auto-user-creation on every employee record."""
import logging
import secrets
import string

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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
            'groups_id': [(6, 0, self.group_ids.ids)],
        })
        self.employee_id.user_id = user.id
        self.employee_id.message_post(body=_(
            'System access granted (login: %(login)s). Ask the doctor to '
            'change the temporary password on first login.', login=self.login))

        # Prefer Odoo's normal signup/reset-password email if outgoing
        # mail is configured; the temporary password is still shown below
        # as a fallback for clinics without SMTP set up yet.
        #
        # 2026-09-20 (afia_dental_core-doctor-invite-swallowed-exception):
        # this used to be a bare `except Exception: pass`, silently
        # discarding ANY failure with no log trace. Odoo core's own
        # action_reset_password() (auth_signup/models/res_users.py)
        # already catches the low-level MailDeliveryException itself and
        # re-raises it as a plain UserError for exactly the "mail not
        # configured" case this fallback exists for — so UserError is the
        # only exception type the anticipated scenario can actually raise
        # here. Anything else is a genuinely unexpected failure and must
        # not be hidden identically. Neither path re-raises: the doctor's
        # user account must still be created successfully even if email
        # delivery fails, matching the original design intent — but now
        # every failure at least leaves a trace for support/debugging.
        try:
            user.action_reset_password()
        except UserError as e:
            _logger.info(
                'dental.doctor.invite: reset-password email not sent for '
                '%s (expected if outgoing mail isn\'t configured yet): %s',
                self.login, e)
        except Exception:
            _logger.exception(
                'dental.doctor.invite: unexpected error sending the '
                'reset-password email for %s. The user account was still '
                'created successfully; only the email failed.', self.login)

        self.write({'temp_password': temp_password, 'state': 'done'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dental.doctor.invite',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
