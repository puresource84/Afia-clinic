from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestVisitBilling(AccountTestInvoicingCommon):
    """Book -> treat -> invoice -> cash payment, through one pipeline."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The accounting fixture runs as a dedicated accountant user; give
        # it the clinic role a front-desk manager would have.
        cls.env.user.groups_id |= cls.env.ref('clinic_core.group_clinic_admin')
        cls.patient = cls.env['res.partner'].create(
            {'name': 'Billing Patient', 'is_patient': True})
        cls.dentist = cls.env['hr.employee'].create(
            {'name': 'Dr. Billing', 'is_dentist': True})
        category = cls.env['treatment.category'].create({'name': 'General'})
        cls.filling = cls.env['dental.treatment'].create({
            'name': 'Filling', 'treatment_categ_id': category.id, 'cost': 50.0})
        cls.scaling = cls.env['dental.treatment'].create({
            'name': 'Scaling', 'treatment_categ_id': category.id, 'cost': 30.0})
        cls.medicine = cls.env['product.template'].create({
            'name': 'Amoxicillin', 'is_medicine': True, 'list_price': 7.0})

    def _visit(self, treatments=None):
        return self.env['dental.appointment'].create({
            'patient_id': self.patient.id,
            'dentist_id': self.dentist.id,
            'treatments': [(6, 0, (treatments or self.filling).ids)],
        })

    def test_flow_done_runs_real_workflow(self):
        apt = self._visit()
        apt.action_flow_done()
        self.assertEqual(apt.state, 'done')
        self.assertEqual(apt.flow_state, 'done')

    def test_flow_invoice_posts_once(self):
        apt = self._visit()
        apt.action_flow_done()
        apt.action_flow_invoice()
        invoice = apt.invoice_ids
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual(invoice.amount_untaxed, 50.0)
        # Clicking again opens the same invoice instead of billing twice.
        action = apt.action_flow_invoice()
        self.assertEqual(action['res_id'], invoice.id)
        self.assertEqual(len(apt.invoice_ids), 1)
        with self.assertRaises(UserError):
            apt.action_create_invoice()

    def test_prescription_billed_on_visit_invoice(self):
        apt = self._visit()
        rx = self.env['dental.prescription'].create({
            'appointment_id': apt.id,
            'treatment_id': self.scaling.id,
            'medicine_ids': [(0, 0, {
                'medicament_id': self.medicine.id,
                'medicament_form': 'tablet',
                'quantity': 2,
            })],
        })
        with self.assertRaises(UserError):
            rx.action_create_invoice()  # visit not completed yet
        rx.action_prescribed()
        self.assertEqual(apt.state, 'done')
        rx.action_create_invoice()
        invoice = apt.invoice_ids
        self.assertEqual(len(invoice), 1, 'one invoice per visit')
        self.assertEqual(rx.state, 'invoiced')
        self.assertEqual(rx.treatment_invoice_id, invoice)
        # filling (appointment) + scaling (prescription) + 2 x 7 medicine
        self.assertEqual(invoice.amount_untaxed, 94.0)

    def test_prescription_treatment_not_billed_twice(self):
        apt = self._visit()
        rx = self.env['dental.prescription'].create({
            'appointment_id': apt.id, 'treatment_id': self.filling.id})
        rx.action_prescribed()
        apt.action_create_invoice()
        self.assertEqual(apt.invoice_ids.amount_untaxed, 50.0)
        rx.action_create_invoice()
        self.assertEqual(len(apt.invoice_ids), 1)

    def test_cash_payment_moves_card_to_paid(self):
        apt = self._visit()
        apt.action_flow_done()
        action = apt.action_flow_paid()
        invoice = apt.invoice_ids
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual(apt.flow_state, 'done',
                         'card must not be Paid before money is received')
        self.assertEqual(action['res_model'], 'account.payment.register')
        cash = self.company_data['default_journal_cash']
        self.assertEqual(action['context'].get('default_journal_id'), cash.id)
        wizard = Form(self.env['account.payment.register'].with_context(
            action['context']))
        wizard.save()._create_payments()
        self.assertIn(invoice.payment_state, ('paid', 'in_payment'))
        self.assertEqual(apt.flow_state, 'paid')

    def test_workflow_guards(self):
        apt = self._visit()
        with self.assertRaises(UserError):
            apt.action_done()  # draft cannot jump to done
        apt.action_confirm()
        apt.action_done()
        with self.assertRaises(UserError):
            apt.action_cancel()  # done visits cannot be cancelled
