# -*- coding: utf-8 -*-
"""Dentist extension of hr.employee. Clean-room rewrite (2026-08).

Previous behavior silently created an internal res.users login (mobile
number as username, no password) on every employee creation, and deleted
the user record outright when the employee was deleted/archived. Per the
2026-08-04 GM decision ("keep the convenience, fix it properly"):
  - user creation is now a deliberate, explicit action (see
    wizard/doctor_invite.py), never automatic on record creation
  - a real random temporary password is generated and shown once,
    instead of no password at all
  - the grant is logged to the employee's chatter for auditability
  - unlink() no longer deletes the linked user; archiving the employee
    archives (deactivates) the user instead, preserving the audit trail
"""
from datetime import date

from odoo import _, api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_dentist = fields.Boolean(string='Is a Dentist', index=True)
    job_position = fields.Char(string='Designation')
    reg_no = fields.Char(string='Register No.')
    specialised_in_id = fields.Many2one('dental.specialist', string='Specialised In')
    dob = fields.Date(string='Date of Birth')
    doctor_age = fields.Integer(compute='_compute_doctor_age', store=True, string='Age')
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Sex')
    time_shift_ids = fields.Many2many('dental.time.shift', string='Time Shifts')
    employee_type = fields.Selection(selection_add=[
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist'),
    ], ondelete={'doctor': 'set default', 'receptionist': 'set default'})

    portal_access_granted = fields.Boolean(
        string='System Access Granted', compute='_compute_portal_access_granted')

    @api.depends('dob')
    def _compute_doctor_age(self):
        today = date.today()
        for rec in self:
            if rec.dob:
                rec.doctor_age = today.year - rec.dob.year - (
                    (today.month, today.day) < (rec.dob.month, rec.dob.day))
            else:
                rec.doctor_age = False

    def _compute_portal_access_granted(self):
        for rec in self:
            rec.portal_access_granted = bool(rec.user_id and rec.user_id.active)

    def action_invite_system_access(self):
        """Open the deliberate invite wizard instead of silently creating
        a login. Available whenever the employee doesn't already have an
        active linked user."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Grant System Access'),
            'res_model': 'dental.doctor.invite',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_employee_id': self.id},
        }

    def action_revoke_system_access(self):
        """Archive (not delete) the linked user — keeps the audit trail
        instead of the old unlink()-cascades-to-unlink() behavior."""
        for rec in self:
            if rec.user_id:
                rec.user_id.active = False
                rec.message_post(body=_(
                    'System access revoked for %(user)s.', user=rec.user_id.name))
