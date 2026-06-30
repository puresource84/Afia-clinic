from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

TEMPLATE_KEYS = [
    ('reminder', 'Appointment Reminder (before visit)'),
    ('review_request', 'Review Request (after visit)'),
    ('recall', 'Recall / Recare Campaign'),
    ('welcome_linked', 'Welcome — Patient Linked'),
    ('patient_not_found', 'Linking Failed — Patient No. Not Found'),
    ('no_upcoming', 'Reply — No Upcoming Appointment'),
    ('confirm_ack', 'Reply — Appointment Confirmed'),
    ('cancel_ack', 'Reply — Appointment Cancelled'),
    ('review_thanks', 'Review Thanks (score 1–4)'),
    ('review_thanks_5', 'Review Thanks (score 5 → review link)'),
]

# keys whose crons honor the offset fields (value + unit + direction)
_TIMED_KEYS = {'reminder', 'review_request'}
# timed keys may have SEVERAL active templates (e.g. reminder 1 day before
# + 1 hour before; post-visit care message 2 hours after + review request
# 1 day after); every other key is single-instance.
_MULTI_KEYS = _TIMED_KEYS


class _SafeDict(dict):
    """Unknown placeholders stay literal instead of crashing the cron."""
    def __missing__(self, key):
        return '{%s}' % key


class DentalTelegramTemplate(models.Model):
    _name = 'dental.telegram.template'
    _description = 'Telegram Message Template'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    template_key = fields.Selection(
        TEMPLATE_KEYS, required=True, copy=False, string='Message',
        help='Which automated message this template controls. The '
             'Appointment Reminder may have several templates with '
             'different offsets (e.g. 1 day before AND 1 hour before).')
    name = fields.Char(required=True, translate=True)
    body = fields.Text(
        required=True, string='Message Text',
        help='Placeholders: {patient_name} {patient_no} {clinic_name} '
             '{date} {time} {shift} {dentist} {review_link}. Unknown '
             'placeholders are left as-is. Keep AR + EN in one message.')
    offset_value = fields.Integer(
        string='Send Offset', default=1,
        help='Reminder: how long BEFORE the appointment. '
             'Review request: how long AFTER the visit.')
    offset_unit = fields.Selection([
        ('days', 'Day(s)'),
        ('hours', 'Hour(s)'),
    ], default='days', required=True, string='Offset Unit',
        help='Hour-based offsets use the appointment time (online-booking '
             'slot, or the shift start time). Appointments without any '
             'time are skipped by hour-based messages.')
    offset_direction = fields.Selection([
        ('before', 'Before the visit'),
        ('after', 'After the visit'),
    ], default='before', required=True, string='Direction',
        help='Before the visit targets confirmed/in-progress appointments '
             '(reminders); after the visit targets DONE appointments '
             '(care instructions, review requests).')
    send_after_hour = fields.Float(
        string='Earliest Send Hour (clinic time)', default=9.0,
        help='Day-offset and recall messages wait until this hour in the '
             'clinic timezone. 9.0 = 09:00. Hour-offset messages and '
             'instant replies ignore this.')
    active = fields.Boolean(default=True)
    show_timing = fields.Boolean(compute='_compute_show_timing')
    show_hour = fields.Boolean(compute='_compute_show_timing')
    test_partner_id = fields.Many2one(
        'res.partner', string='Send Test To',
        domain=[('telegram_chat_id', '!=', False)],
        help='A Telegram-linked patient to receive a [TEST] message.')

    _sql_constraints = [
        ('template_key_uniq',
         'unique(template_key, offset_value, offset_unit, offset_direction)',
         'A template for this message with the same offset already exists.'),
    ]

    @api.constrains('template_key', 'active')
    def _check_single_instance_keys(self):
        for t in self:
            if t.template_key in _MULTI_KEYS or not t.active:
                continue
            dupes = self.search_count([
                ('template_key', '=', t.template_key),
                ('active', '=', True), ('id', '!=', t.id)])
            if dupes:
                raise ValidationError(_(
                    'Only the timed messages (Reminder / Review Request) may '
                    'have several active templates. "%s" already has one — '
                    'edit it instead.'
                ) % dict(TEMPLATE_KEYS)[t.template_key])

    @api.onchange('template_key')
    def _onchange_template_key_direction(self):
        if self.template_key == 'review_request':
            self.offset_direction = 'after'
        elif self.template_key == 'reminder':
            self.offset_direction = 'before'

    @api.depends('template_key', 'offset_unit')
    def _compute_show_timing(self):
        for t in self:
            t.show_timing = t.template_key in _TIMED_KEYS
            t.show_hour = (
                t.template_key == 'recall'
                or (t.template_key in _TIMED_KEYS
                    and t.offset_unit == 'days'))

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _render(self, ctx):
        self.ensure_one()
        return (self.body or '').format_map(_SafeDict(ctx or {}))

    @api.model
    def _get(self, key):
        """All active templates for a key, ordered."""
        return self.sudo().search(
            [('template_key', '=', key), ('active', '=', True)])

    @api.model
    def _render_key(self, key, ctx):
        """Rendered body of the FIRST active template for key, or None →
        caller uses the built-in fallback text."""
        tmpl = self._get(key)[:1]
        return tmpl._render(ctx) if tmpl else None

    # ------------------------------------------------------------------
    # Test send
    # ------------------------------------------------------------------
    def action_send_test(self):
        self.ensure_one()
        partner = self.test_partner_id
        if not (partner and partner.telegram_chat_id):
            raise UserError(_(
                'Pick a Telegram-linked patient in "Send Test To" first '
                '(patients link via the bot deep link).'))
        Apt = self.env['dental.appointment']
        apt = Apt.search([('patient_id', '=', partner.id)],
                         order='id desc', limit=1)
        ctx = Apt._tg_template_ctx(apt=apt or None, patient=partner)
        body = '[TEST] %s' % self._render(ctx)
        if not Apt._tg_send(partner.telegram_chat_id, body):
            raise UserError(_(
                'Telegram send failed — check that Telegram is enabled and '
                'the bot token is valid (Settings → Clinic Core → Telegram).'))
        self.env['dental.telegram.message.log'].sudo().create({
            'appointment_id': apt.id if apt else False,
            'patient_id': partner.id,
            'template_id': self.id,
            'template_key': self.template_key,
            'body': body,
            'is_test': True,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _('Test message sent to %s.') % partner.name,
                'sticky': False,
            },
        }


class DentalTelegramMessageLog(models.Model):
    """Every outbound patient message: per-template dedupe for multi-stage
    reminders + a visibility page for the front desk."""
    _name = 'dental.telegram.message.log'
    _description = 'Telegram Sent Message'
    _order = 'sent_date desc, id desc'
    _rec_name = 'template_key'

    appointment_id = fields.Many2one(
        'dental.appointment', string='Appointment', index=True,
        ondelete='cascade')
    patient_id = fields.Many2one(
        'res.partner', string='Patient', index=True, ondelete='cascade')
    template_id = fields.Many2one(
        'dental.telegram.template', string='Template', ondelete='set null')
    template_key = fields.Char(string='Message Type', index=True)
    body = fields.Text(string='Message')
    sent_date = fields.Datetime(
        string='Sent At', default=fields.Datetime.now, index=True)
    is_test = fields.Boolean(string='Test', default=False)

    @api.model
    def _already_sent(self, apt, tmpl):
        return bool(self.sudo().search_count([
            ('appointment_id', '=', apt.id),
            ('template_id', '=', tmpl.id),
            ('is_test', '=', False)]))

    @api.model
    def _log(self, tmpl, body, apt=None, patient=None):
        return self.sudo().create({
            'appointment_id': apt.id if apt else False,
            'patient_id': (patient or (apt and apt.patient_id)).id
            if (patient or apt) else False,
            'template_id': tmpl.id if tmpl else False,
            'template_key': tmpl.template_key if tmpl else '',
            'body': body,
        })
