# -*- coding: utf-8 -*-
"""Which menus each clinic role is shown.

Every defect the 2026-10-31 browser pass turned up was a menu, view or
asset fault, not an access-rights fault: a Perio Exams menu the hygienist
could not reach though the ACLs allowed it, Configuration reachable by a
dentist, two buttons whose owning views were in no manifest. The suite's
existing role tests all assert model permissions, so none of them could
have caught any of it.

This asserts the other half: what the navigation actually renders for a
given role. afia_menu is the right home because it depends on every other
module, so the whole menu tree exists by the time these run.
"""
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestRoleMenus(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        core = 'afia_dental_core.group_clinic_%s'
        cls.receptionist = new_test_user(
            cls.env, login='afia_menu_reception', groups=core % 'receptionist')
        cls.hygienist = new_test_user(
            cls.env, login='afia_menu_hygienist', groups=core % 'hygienist')
        cls.dentist = new_test_user(
            cls.env, login='afia_menu_dentist', groups=core % 'dentist')
        cls.owner_dentist = new_test_user(
            cls.env, login='afia_menu_owner', groups=core % 'admin')

    def _visible(self, user):
        """Menu ids this user is actually served.

        load_menus is what the web client calls, so it reflects the rendered
        tree rather than raw group membership — including Odoo dropping the
        children of a menu the user cannot see.
        """
        menus = self.env['ir.ui.menu'].with_user(user).load_menus(False)
        return {k for k in menus if isinstance(k, int)}

    def _id(self, xmlid):
        return self.env.ref(xmlid).id

    # ── configuration is clinic administration ───────────────────────────

    def test_configuration_hidden_from_clinical_roles(self):
        config = self._id('afia_dental_core.dental_configure')
        for role, user in (('receptionist', self.receptionist),
                           ('hygienist', self.hygienist),
                           ('dentist', self.dentist)):
            self.assertNotIn(
                config, self._visible(user),
                'the %s must not reach clinic Configuration' % role)

    def test_owner_dentist_reaches_configuration(self):
        self.assertIn(
            self._id('afia_dental_core.dental_configure'),
            self._visible(self.owner_dentist),
            'a dentist who also manages the clinic needs Configuration')

    def test_staff_accounts_are_administrator_only(self):
        staff = self._id('afia_dental_core.dental_staff')
        self.assertNotIn(staff, self._visible(self.dentist))
        self.assertIn(staff, self._visible(self.owner_dentist))

    # ── clinical menus ───────────────────────────────────────────────────

    def test_hygienist_reaches_perio_exams(self):
        perio = self._id('dental_charting.menu_perio_exams')
        self.assertIn(perio, self._visible(self.hygienist),
                      'periodontal charting is hygienist work')
        self.assertIn(perio, self._visible(self.dentist))
        self.assertNotIn(perio, self._visible(self.receptionist))

    def test_clinical_notes_are_dentist_and_above(self):
        notes = self._id('dental_soap_notes.menu_soap_notes')
        self.assertIn(notes, self._visible(self.dentist))
        self.assertNotIn(notes, self._visible(self.receptionist))

    # ── the clinical roles still get a usable clinic ─────────────────────
    # A restriction that empties the app is as broken as one that leaks.

    def test_every_role_still_has_a_clinic_to_work_in(self):
        root = self._id('afia_dental_core.hospital_root_menu')
        for role, user in (('receptionist', self.receptionist),
                           ('hygienist', self.hygienist),
                           ('dentist', self.dentist),
                           ('owner dentist', self.owner_dentist)):
            visible = self._visible(user)
            self.assertIn(root, visible,
                          'the %s must still see the clinic app' % role)
            self.assertGreater(
                len(visible), 5,
                'the %s was left with an almost empty menu' % role)
