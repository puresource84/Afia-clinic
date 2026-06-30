from unittest.mock import patch, MagicMock

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

MODPATH = 'odoo.addons.dental_reminders_telegram.models.dental_telegram'


@tagged('post_install', '-at_install')
class TestTelegramReminders(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Appointment = cls.env['dental.appointment']
        cls.patient = cls.env['res.partner'].create({
            'name': 'Tg Test Patient', 'is_patient': True,
            'patient_no': 'PTTEST01', 'telegram_chat_id': '12345'})
        cls.env['ir.config_parameter'].sudo().set_param(
            'dental_telegram.bot_token', 'test:token')

    def test_send_without_token_returns_false(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'dental_telegram.bot_token', '')
        self.assertFalse(self.Appointment._tg_send('12345', 'hi'))

    @patch(MODPATH + '.requests.post')
    def test_send_success(self, mock_post):
        mock_post.return_value = MagicMock(
            json=lambda: {'ok': True, 'result': {'message_id': 1}})
        self.assertTrue(self.Appointment._tg_send('12345', 'hello'))
        args, kwargs = mock_post.call_args
        self.assertIn('sendMessage', args[0])
        self.assertEqual(kwargs['json']['chat_id'], '12345')

    @patch(MODPATH + '.requests.post')
    def test_gateway_error_never_raises(self, mock_post):
        mock_post.side_effect = Exception('down')
        self.assertFalse(self.Appointment._tg_send('12345', 'hi'))

    @patch(MODPATH + '.requests.post')
    def test_polling_links_patient(self, mock_post):
        self.patient.telegram_chat_id = False
        mock_post.return_value = MagicMock(json=lambda: {'ok': True, 'result': [
            {'update_id': 7, 'message': {
                'text': '/start PTTEST01', 'chat': {'id': 999}}}]})
        self.Appointment._cron_poll_telegram_updates()
        self.assertEqual(self.patient.telegram_chat_id, '999',
                         'deep-link /start must link the patient chat id')
        self.assertEqual(self.env['ir.config_parameter'].sudo().get_param(
            'dental_telegram.last_update_id'), '7')

    def test_reminder_body_bilingual(self):
        apt = self.Appointment.new({
            'patient_id': self.patient.id,
            'appointment_date': fields.Date.today(),
        })
        body = self.Appointment._tg_reminder_body(apt)
        self.assertIn('Tg Test Patient', body)
        self.assertIn('نذكّركم', body)
