# -*- coding: utf-8 -*-
"""Regression guard for the ACL gap found in the 2026-09-20 system audit
(Domain A2): dental.lab.order used to grant full CRUD to base.group_user
(every internal user). Fixed by demoting that row to read-only and adding
a role-scoped grant to afia_dental_core.group_dental_reception."""
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLabOrderAccessControl(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reception_group = cls.env.ref('afia_dental_core.group_dental_reception')
        cls.bare_user = cls.env['res.users'].create({
            'name': 'Bare Internal User', 'login': 'bare_user_lab_test',
        })
        cls.reception_user = cls.env['res.users'].create({
            'name': 'Reception User', 'login': 'reception_user_lab_test',
            'group_ids': [(6, 0, [cls.reception_group.id])],
        })
        cls.patient = cls.env['res.partner'].create({'name': 'Lab Patient', 'is_patient': True})

    def test_bare_internal_user_cannot_create_lab_order(self):
        with self.assertRaises(AccessError):
            self.env['dental.lab.order'].with_user(self.bare_user).create({
                'patient_id': self.patient.id,
                'lab_name': 'Test Lab',
                'due_date': '2026-12-01',
            })

    def test_reception_user_can_create_and_write_lab_order(self):
        order = self.env['dental.lab.order'].with_user(self.reception_user).create({
            'patient_id': self.patient.id,
            'lab_name': 'Test Lab',
            'due_date': '2026-12-01',
        })
        order.write({'shade': 'A2'})
        self.assertEqual(order.shade, 'A2')

    def test_bare_internal_user_can_still_read(self):
        order = self.env['dental.lab.order'].create({
            'patient_id': self.patient.id,
            'lab_name': 'Test Lab',
            'due_date': '2026-12-01',
        })
        order_as_bare = order.with_user(self.bare_user)
        self.assertTrue(order_as_bare.lab_name)
        with self.assertRaises(AccessError):
            order_as_bare.write({'shade': 'B1'})
