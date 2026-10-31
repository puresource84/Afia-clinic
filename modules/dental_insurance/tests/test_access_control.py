# -*- coding: utf-8 -*-
"""Regression guard for the ACL gap found in the 2026-09-20 system audit
(Domain A1): dental.insurer/dental.policy/dental.claim used to grant full
CRUD to base.group_user (every internal user, regardless of clinic role).
Fixed by demoting that row to read-only and adding a proper role-scoped
grant to afia_dental_core.group_clinic_receptionist (which cascades up to
Dentist and Clinic Administrator via implied_ids)."""
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestInsuranceAccessControl(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reception_group = cls.env.ref('afia_dental_core.group_clinic_receptionist')
        cls.bare_user = cls.env['res.users'].create({
            'name': 'Bare Internal User', 'login': 'bare_user_insurance_test',
        })
        cls.reception_user = cls.env['res.users'].create({
            'name': 'Reception User', 'login': 'reception_user_insurance_test',
            # Odoo 18 field name is groups_id; group_ids is the 19/20 spelling.
            'groups_id': [(6, 0, [cls.reception_group.id])],
        })
        cls.insurer = cls.env['dental.insurer'].create({'name': 'Test Insurer'})

    def test_bare_internal_user_can_read_but_not_write_insurer(self):
        insurer_as_bare = self.insurer.with_user(self.bare_user)
        self.assertTrue(insurer_as_bare.name)  # read works
        with self.assertRaises(AccessError):
            insurer_as_bare.write({'name': 'Hacked Name'})

    def test_bare_internal_user_cannot_create_claim(self):
        patient = self.env['res.partner'].create({'name': 'Claim Patient', 'is_patient': True})
        policy = self.env['dental.policy'].create({
            'name': 'POL-TEST-1', 'insurer_id': self.insurer.id, 'patient_id': patient.id,
        })
        with self.assertRaises(AccessError):
            self.env['dental.claim'].with_user(self.bare_user).create({
                'patient_id': patient.id, 'policy_id': policy.id,
            })

    def test_reception_user_can_create_and_write_claim(self):
        patient = self.env['res.partner'].create({'name': 'Claim Patient 2', 'is_patient': True})
        policy = self.env['dental.policy'].with_user(self.reception_user).create({
            'name': 'POL-TEST-2', 'insurer_id': self.insurer.id, 'patient_id': patient.id,
        })
        claim = self.env['dental.claim'].with_user(self.reception_user).create({
            'patient_id': patient.id, 'policy_id': policy.id,
        })
        claim.write({'total_amount': 100.0})
        self.assertEqual(claim.total_amount, 100.0)
