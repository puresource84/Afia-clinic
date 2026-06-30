from unittest.mock import patch, MagicMock

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWhatsAppReminders(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Appointment = cls.env['dental.appointment']
        cls.patient = cls.env['res.partner'].create({
            'name': 'Wa Test Patient', 'is_patient': True,
            'mobile': '+964 770 000 0000'})
        cls.env['ir.config_parameter'].sudo().set_param(
            'dental_whatsapp.api_url', 'https://gateway.test/messages')
        cls.env['ir.config_parameter'].sudo().set_param(
            'dental_whatsapp.api_token', 'test-token')

    def test_send_no_config_returns_false(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'dental_whatsapp.api_url', '')
        self.assertFalse(self.Appointment._wa_send('+964770', 'hi'))

    @patch('odoo.addons.dental_reminders_whatsapp.models.dental_whatsapp.requests.post')
    def test_send_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        ok = self.Appointment._wa_send('+964 770 000 0000', 'hello')
        self.assertTrue(ok)
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['to'], '+9647700000000',
                         'phone must be normalized to digits/+')
        self.assertIn('Bearer test-token',
                      kwargs['headers']['Authorization'])

    @patch('odoo.addons.dental_reminders_whatsapp.models.dental_whatsapp.requests.post')
    def test_send_gateway_error_never_raises(self, mock_post):
        mock_post.side_effect = Exception('network down')
        self.assertFalse(self.Appointment._wa_send('+964770', 'hi'))

    def test_reminder_body_bilingual(self):
        apt = self.Appointment.new({
            'patient_id': self.patient.id,
            'appointment_date': fields.Date.today(),
        })
        body = self.Appointment._wa_reminder_body(apt)
        self.assertIn('Wa Test Patient', body)
        self.assertIn('نذكّركم', body, 'Arabic half must be present')
