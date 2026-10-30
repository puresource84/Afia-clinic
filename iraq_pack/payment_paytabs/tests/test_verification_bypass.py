# -*- coding: utf-8 -*-
"""Regression guard for afia_dental_core-paytabs-verification-bypass
(2026-09-20 system audit, Domain B1): _process_notification_data used to
fall back to trusting the RAW, unverified webhook payload whenever
server-side verification raised. Fixed to never mark a transaction
done/failed from unverified data — it's left pending instead, so a
forged callback can never buy a "done" status by making verification
fail."""
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPayTabsVerificationBypass(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env['payment.provider'].create({
            'name': 'PayTabs Test',
            'code': 'paytabs',
            'state': 'test',
            'paytabs_profile_id': 'test-profile',
            'paytabs_server_key': 'test-key',
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Payer'})
        cls.tx = cls.env['payment.transaction'].create({
            'provider_id': cls.provider.id,
            'payment_method_id': cls.env.ref('payment.payment_method_unknown').id,
            'amount': 10.0,
            'currency_id': cls.env.ref('base.USD').id,
            'partner_id': cls.partner.id,
            'reference': 'TEST-TX-001',
            'provider_reference': 'PT-TRAN-REF-001',
        })

    def test_verification_failure_never_marks_transaction_done(self):
        """Even if the (forged) raw callback claims an approved status,
        a verification failure must leave the transaction pending, never
        done — this is the exact vulnerability being closed."""
        forged_notification_data = {
            'tran_ref': 'PT-TRAN-REF-001',
            'response': {'response_status': 'A', 'response_message': 'Approved (forged)'},
        }
        with patch(
            'odoo.addons.payment_paytabs.models.payment_provider.'
            'PaymentProviderPayTabs._paytabs_verify_transaction',
            side_effect=Exception('simulated verification failure'),
        ):
            self.tx._process_notification_data(forged_notification_data)
        self.assertNotEqual(
            self.tx.state, 'done',
            'A transaction must never be marked done from unverified '
            'callback data when server-side verification fails.')
        self.assertEqual(self.tx.state, 'pending')

    def test_successful_verification_still_marks_done(self):
        """Sanity check: the legitimate path (verification succeeds,
        returns an approved status) must still work after the fix."""
        with patch(
            'odoo.addons.payment_paytabs.models.payment_provider.'
            'PaymentProviderPayTabs._paytabs_verify_transaction',
            return_value={'response': {'response_status': 'A'}},
        ):
            self.tx._process_notification_data({'tran_ref': 'PT-TRAN-REF-001'})
        self.assertEqual(self.tx.state, 'done')
