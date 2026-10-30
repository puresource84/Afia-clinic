# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDentalPrescription(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.patient = cls.env['res.partner'].create({
            'name': 'Rx Patient', 'is_patient': True,
        })
        cls.dentist_employee = cls.env['hr.employee'].create({
            'name': 'Dr. Rx', 'is_dentist': True,
        })
        cls.appointment = cls.env['dental.appointment'].create({
            'patient_id': cls.patient.id,
            'dentist_id': cls.dentist_employee.id,
        })
        cls.treatment_category = cls.env['treatment.category'].create({
            'name': 'Test Category',
        })
        cls.treatment = cls.env['dental.treatment'].create({
            'name': 'Filling',
            'treatment_categ_id': cls.treatment_category.id,
            'cost': 50.0,
        })
        # Fresh test databases (without_demo=True) have no chart of
        # accounts at all — no income account, no receivable account, no
        # sales journal. Not an afia_dental_core concern (real installs
        # always have Accounting configured), but the test needs to
        # build its own minimal CoA to be self-contained regardless of
        # demo data.
        company = cls.env.company
        if not company.partner_id.property_account_receivable_id:
            receivable_account = cls.env['account.account'].create({
                'name': 'Test Receivable Account',
                'code': '110000',
                'account_type': 'asset_receivable',
                'reconcile': True,
                'company_ids': [(6, 0, [company.id])],
            })
            company.partner_id.with_company(company).property_account_receivable_id = receivable_account

        sale_journal = cls.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
        if not sale_journal or not sale_journal.default_account_id:
            income_account = cls.env['account.account'].create({
                'name': 'Test Income Account',
                'code': '400000',
                'account_type': 'income',
                'company_ids': [(6, 0, [company.id])],
            })
            if sale_journal:
                sale_journal.default_account_id = income_account
            else:
                cls.env['account.journal'].create({
                    'name': 'Test Sales Journal',
                    'type': 'sale',
                    'code': 'TSJ',
                    'company_id': company.id,
                    'default_account_id': income_account.id,
                })

    def test_sequence_assigned_on_create(self):
        rx = self.env['dental.prescription'].create({
            'appointment_id': self.appointment.id,
        })
        self.assertNotEqual(rx.sequence_no, 'New')

    def test_patient_and_doctor_follow_appointment(self):
        rx = self.env['dental.prescription'].create({
            'appointment_id': self.appointment.id,
        })
        self.assertEqual(rx.patient_id, self.patient)
        self.assertEqual(rx.prescribed_doctor_id, self.dentist_employee)

    def test_next_appointment_date_creates_follow_up(self):
        rx = self.env['dental.prescription'].create({
            'appointment_id': self.appointment.id,
        })
        existing = self.env['dental.appointment'].search([
            ('patient_id', '=', self.patient.id),
        ])
        rx.write({'next_appointment_date': '2026-09-01'})
        follow_ups = self.env['dental.appointment'].search([
            ('patient_id', '=', self.patient.id),
        ]) - existing
        self.assertTrue(follow_ups)
        self.assertEqual(follow_ups.state, 'draft')

    def test_action_prescribed_closes_appointment(self):
        rx = self.env['dental.prescription'].create({
            'appointment_id': self.appointment.id,
        })
        rx.action_prescribed()
        self.assertEqual(rx.state, 'done')
        self.assertEqual(self.appointment.state, 'done')

    def test_action_create_invoice_requires_treatment(self):
        rx = self.env['dental.prescription'].create({
            'appointment_id': self.appointment.id,
        })
        with self.assertRaises(Exception):
            rx.action_create_invoice()

    def test_action_create_invoice_creates_treatment_invoice(self):
        rx = self.env['dental.prescription'].create({
            'appointment_id': self.appointment.id,
            'treatment_id': self.treatment.id,
        })
        rx.action_prescribed()
        rx.action_create_invoice()
        self.assertEqual(rx.state, 'invoiced')
        self.assertTrue(rx.treatment_invoice_id)
        self.assertEqual(rx.treatment_invoice_id.amount_total, 50.0)
