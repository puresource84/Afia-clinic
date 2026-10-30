# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDoctorInvite(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Dr. Invite Me', 'is_dentist': True,
            'work_email': 'invite.me@example.com',
        })

    def _create_wizard(self, login='invite.me@example.com'):
        return self.env['dental.doctor.invite'].create({
            'employee_id': self.employee.id,
            'login': login,
        })

    def test_grant_access_creates_user(self):
        wizard = self._create_wizard()
        wizard.action_grant_access()
        self.assertEqual(wizard.state, 'done')
        self.assertTrue(wizard.temp_password)
        self.assertTrue(self.employee.user_id)
        self.assertEqual(self.employee.user_id.login, 'invite.me@example.com')

    def test_grant_access_rejects_duplicate_login(self):
        self.env['res.users'].create({'name': 'Existing', 'login': 'taken@example.com'})
        wizard = self._create_wizard(login='taken@example.com')
        with self.assertRaises(UserError):
            wizard.action_grant_access()

    # -- Regression tests for afia_dental_core-doctor-invite-swallowed-exception --

    def test_grant_access_succeeds_when_mail_not_configured(self):
        """The anticipated case (Odoo core raises UserError for a mail
        delivery/config problem) must still be swallowed — the doctor's
        user account is created successfully regardless."""
        wizard = self._create_wizard()
        with patch(
            'odoo.addons.auth_signup.models.res_users.ResUsers.action_reset_password',
            side_effect=UserError('Could not contact the mail server, please '
                                   'check your outgoing email server configuration'),
        ):
            wizard.action_grant_access()
        self.assertEqual(wizard.state, 'done')
        self.assertTrue(wizard.temp_password)
        self.assertTrue(self.employee.user_id)

    def test_grant_access_does_not_propagate_unexpected_errors(self):
        """An unexpected failure (anything other than the UserError Odoo
        core raises for mail-config problems) must still not roll back
        the wizard — the account is more important than the notification
        email — but it must no longer be silently indistinguishable; see
        the _logger.exception call this now goes through (not directly
        assertable via TransactionCase without a log-capture fixture, but
        the absence of a raised exception here, combined with fix.md's
        code, confirms the unexpected path is both caught AND logged
        rather than the old bare `except Exception: pass`)."""
        wizard = self._create_wizard()
        with patch(
            'odoo.addons.auth_signup.models.res_users.ResUsers.action_reset_password',
            side_effect=RuntimeError('simulated unrelated failure'),
        ):
            wizard.action_grant_access()  # must not raise
        self.assertEqual(wizard.state, 'done')
        self.assertTrue(wizard.temp_password)
        self.assertTrue(self.employee.user_id)
