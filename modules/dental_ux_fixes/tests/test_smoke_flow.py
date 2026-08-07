# -*- coding: utf-8 -*-
"""
Cross-module smoke test for the Afia Clinic core flow.

Exercises, at the ORM level:
    patient -> appointment -> treatment plan session -> treatment done
    -> consumable stock deduction (dental_consumables BOM) -> invoice
    -> state transitions.

Lives in dental_ux_fixes because that is the first module in the
dependency graph whose __manifest__.py already pulls in every module
this test touches (afia_dental_core, dental_treatment_plan,
dental_consumables via clinic_core, stock, account). Putting it in
afia_dental_core itself is not possible without adding test-only
dependencies to a module that ships to production.

NOTE (QA, 2026-07-03): this is static-reviewed test CODE, not a executed
result. It has NOT been run against a live Odoo server in this sandbox
(no odoo-bin / postgres available here). Field names, model names and
method names were verified by reading the actual source of afia_dental_core,
dental_treatment_plan, dental_consumables and account in this package as
of 2026-07-03. See QA_REGRESSION_PROGRESS_2026-07-03.md for the confidence
write-up and known gaps.
"""
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAfiaCoreSmokeFlow(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # --- Dentist (hr.employee, is_dentist=True) ---------------------
        # dob is required=True (afia_dental_core/models/dental_doctor.py).
        # Deliberately NOT setting mobile_phone: dental_doctor.py's
        # create() override auto-provisions a res.users login when
        # mobile_phone is set, which is an unwanted side effect here.
        cls.dentist = cls.env['hr.employee'].create({
            'name': 'Dr. Smoke Test',
            'dob': '1985-01-01',
            'is_dentist': True,
        })

        # --- Patient (res.partner, is_patient=True) ----------------------
        cls.patient = cls.env['res.partner'].create({
            'name': 'Smoke Test Patient',
            'is_patient': True,
            'gender': 'male',
            'dob': '1990-05-15',
        })

        # --- Consumable product used by the treatment BOM -----------------
        cls.consumable_product = cls.env['product.product'].create({
            'name': 'Composite Resin (Smoke Test)',
            'type': 'consu',
            'is_storable': True,
        })

        # Give the product stock so the internal->production/customer move
        # can actually be delivered. Use an inventory adjustment via
        # stock.quant so we don't depend on purchase/manufacturing flows.
        internal_loc = cls.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        if internal_loc:
            cls.env['stock.quant']._update_available_quantity(
                cls.consumable_product, internal_loc, 50.0)

        # --- Treatment catalogue entry with a consumable BOM line --------
        cls.treatment = cls.env['dental.treatment'].create({
            'name': 'Composite Filling (Smoke Test)',
            'cost': 150.0,
        })
        cls.env['dental.treatment.consumable'].create({
            'treatment_id': cls.treatment.id,
            'product_id': cls.consumable_product.id,
            'quantity': 2.0,
        })

    def test_01_treatment_bom_flags_product_as_clinic_consumable(self):
        """Adding a treatment BOM line must auto-flag the product
        (dental_consumables.DentalTreatmentConsumable._flag_products_as_consumable)."""
        self.assertTrue(
            self.consumable_product.is_clinic_consumable,
            'product used in a treatment BOM line must be auto-flagged '
            'is_clinic_consumable')

    def test_02_full_patient_to_invoice_flow(self):
        # 1. Create appointment (draft -> confirmed -> in_progress -> done)
        appointment = self.env['dental.appointment'].create({
            'patient_id': self.patient.id,
            'dentist_id': self.dentist.id,
            'appointment_date': '2026-07-10',
            'treatments': [(6, 0, [self.treatment.id])],
        })
        self.assertEqual(appointment.state, 'draft')
        self.assertTrue(
            appointment.appointment_no,
            'appointment_no must be auto-assigned from the ir.sequence '
            'in create() (afia_dental_core/models/dental_appointment.py)')
        self.assertTrue(
            appointment.patient_no,
            'patient_no must be propagated from the patient in create()')

        appointment.action_confirm()
        self.assertEqual(appointment.state, 'confirmed')

        # action_open_patient_form() flips confirmed -> in_progress as a
        # side effect of "opening" the patient form; call it directly
        # rather than simulating a UI click.
        appointment.action_open_patient_form()
        self.assertEqual(appointment.state, 'in_progress')

        # 2. Attach the appointment to a treatment plan session
        plan = self.env['dental.treatment.plan'].create({
            'patient_id': self.patient.id,
            'dentist_id': self.dentist.id,
            'diagnosis': 'Smoke test diagnosis',
        })
        self.assertNotEqual(
            plan.name, '/',
            'plan name/ref must be assigned from ir.sequence '
            '"dental.treatment.plan" in create()')

        plan_line = self.env['dental.treatment.plan.line'].create({
            'plan_id': plan.id,
            'name': 'Session 1 — Composite filling',
            'treatment_ids': [(6, 0, [self.treatment.id])],
            'appointment_id': appointment.id,
            'cost': self.treatment.cost,
        })
        plan.action_start()
        self.assertEqual(plan.state, 'in_progress')
        self.assertEqual(plan.total_sessions, 1)
        self.assertEqual(plan.completed_sessions, 0)

        # 3. Mark appointment done -> triggers consumable stock deduction
        #    (dental_consumables.DentalAppointmentConsume.action_done)
        qty_before = self.env['stock.quant']._get_available_quantity(
            self.consumable_product,
            self.env['stock.location'].search(
                [('usage', '=', 'internal'),
                 ('company_id', '=', self.env.company.id)], limit=1),
        )
        appointment.action_done()
        self.assertEqual(appointment.state, 'done')

        # Consumption is wrapped in try/except in the product code (never
        # blocks Done). Assert it *did* record moves in a normally
        # configured DB, but don't hard-fail the whole test on stock
        # config drift — surface it as a soft assertion via message_post
        # instead, matching the module's own philosophy of "never block
        # Done".
        self.assertTrue(
            appointment.consumption_move_ids,
            'expected stock.move(s) linked via dental_appointment_id after '
            'action_done(); if this fails, check that an internal + '
            'production/customer stock.location exists for the test '
            'company (see _consume_treatment_materials in '
            'dental_consumables/models/dental_consumables.py)')
        self.assertTrue(
            all(m.state == 'done' for m in appointment.consumption_move_ids),
            'all consumption stock moves should reach state=done')

        internal_loc = self.env['stock.location'].search(
            [('usage', '=', 'internal'),
             ('company_id', '=', self.env.company.id)], limit=1)
        qty_after = self.env['stock.quant']._get_available_quantity(
            self.consumable_product, internal_loc)
        self.assertAlmostEqual(
            qty_before - qty_after, 2.0, places=2,
            msg='2.0 units of consumable should be deducted per the BOM '
                'quantity on dental.treatment.consumable')

        # Reflect completion back onto the treatment plan line + plan
        plan_line.write({'state': 'done'})
        self.assertEqual(plan.completed_sessions, 1)
        self.assertEqual(plan.progress_pct, 100.0)
        plan.action_complete()
        self.assertEqual(plan.state, 'completed')

        # 4. Create invoice from the completed appointment
        #    (dental_ux_fixes.DentalAppointmentInvoicing.action_create_invoice)
        action = appointment.action_create_invoice()
        self.assertEqual(appointment.invoice_count, 1)
        invoice = appointment.invoice_ids[0]
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertTrue(invoice.is_treatment_invoice)
        self.assertEqual(invoice.partner_id, self.patient)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit,
                          self.treatment.cost)
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(action['res_id'], invoice.id)

        # 5. Post the invoice and check the standard Odoo state transition
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_03_cannot_invoice_appointment_not_done(self):
        """action_create_invoice must refuse non-done appointments
        (UserError guard in dental_ux_fixes/models/appointment_invoicing.py)."""
        from odoo.exceptions import UserError

        appointment = self.env['dental.appointment'].create({
            'patient_id': self.patient.id,
            'dentist_id': self.dentist.id,
            'appointment_date': '2026-07-11',
            'treatments': [(6, 0, [self.treatment.id])],
        })
        self.assertEqual(appointment.state, 'draft')
        with self.assertRaises(UserError):
            appointment.action_create_invoice()

    def test_04_cannot_invoice_appointment_without_treatments(self):
        appointment = self.env['dental.appointment'].create({
            'patient_id': self.patient.id,
            'dentist_id': self.dentist.id,
            'appointment_date': '2026-07-11',
        })
        appointment.action_confirm()
        appointment.action_open_patient_form()
        appointment.action_done()
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            appointment.action_create_invoice()

    def test_05_appointment_cancel(self):
        appointment = self.env['dental.appointment'].create({
            'patient_id': self.patient.id,
            'dentist_id': self.dentist.id,
            'appointment_date': '2026-07-12',
        })
        appointment.action_cancel()
        self.assertEqual(appointment.state, 'cancelled')
