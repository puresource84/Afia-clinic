from unittest.mock import patch, MagicMock

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

MODPATH = 'odoo.addons.dental_reminders.models.dental_telegram'


@tagged('post_install', '-at_install')
class TestTelegramReminders(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Appointment = cls.env['dental.appointment']
        cls.patient = cls.env['res.partner'].create({
            'name': 'Tg Test Patient', 'is_patient': True,
            'patient_no': 'PTTEST01', 'telegram_chat_id': '12345'})
        icp = cls.env['ir.config_parameter'].sudo()
        icp.set_param('dental_telegram.bot_token', 'test:token')
        # Master switch added after these tests were written; without it
        # _tg_token() returns None and nothing is ever sent or polled.
        icp.set_param('dental_telegram.enabled', 'True')

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

    def _poll(self, mock_post, text, chat_id=999, update_id=7):
        mock_post.return_value = MagicMock(json=lambda: {'ok': True, 'result': [
            {'update_id': update_id, 'message': {
                'text': text, 'chat': {'id': chat_id}}}]})
        self.Appointment._cron_poll_telegram_updates()

    @patch(MODPATH + '.requests.post')
    def test_polling_links_patient(self, mock_post):
        self.patient.telegram_chat_id = False
        token = self.patient._tg_get_link_token()
        self._poll(mock_post, '/start %s' % token)
        self.assertEqual(self.patient.telegram_chat_id, '999',
                         'deep-link /start must link the patient chat id')
        self.assertFalse(self.patient.telegram_link_token,
                         'link token must be single-use')
        self.assertEqual(self.env['ir.config_parameter'].sudo().get_param(
            'dental_telegram.last_update_id'), '7')

    @patch(MODPATH + '.requests.post')
    def test_patient_number_cannot_hijack_chat(self, mock_post):
        """Patient numbers are guessable; /start <patient_no> must not
        link a stranger's chat to the patient."""
        self._poll(mock_post, '/start PTTEST01', chat_id=666)
        self.assertEqual(self.patient.telegram_chat_id, '12345')

    @patch(MODPATH + '.requests.post')
    def test_used_token_cannot_relink(self, mock_post):
        token = self.patient._tg_get_link_token()
        self._poll(mock_post, '/start %s' % token, chat_id=111, update_id=8)
        self._poll(mock_post, '/start %s' % token, chat_id=666, update_id=9)
        self.assertEqual(self.patient.telegram_chat_id, '111')

    def test_deep_link_uses_token_not_patient_no(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'dental_telegram.bot_username', '@afia_bot')
        link = self.patient._tg_deep_link()
        self.assertTrue(link.startswith('https://t.me/afia_bot?start='))
        self.assertNotIn('PTTEST01', link)
        self.assertEqual(link, self.patient._tg_deep_link(),
                         'token is stable until consumed')

    def test_reminder_body_bilingual(self):
        apt = self.Appointment.new({
            'patient_id': self.patient.id,
            'appointment_date': fields.Date.today(),
        })
        body = self.Appointment._tg_reminder_body(apt)
        self.assertIn('Tg Test Patient', body)
        self.assertIn('نذكّركم', body)
