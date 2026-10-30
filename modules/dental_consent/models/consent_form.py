from odoo import models, fields, api


class DentalConsentForm(models.Model):
    _name = 'dental.consent.form'
    _description = 'Patient Consent Form'
    _inherit = ['mail.thread']
    _order = 'signed_date desc, create_date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='/')
    template_id = fields.Many2one('dental.consent.template', required=True)
    patient_id = fields.Many2one('res.partner', required=True,
        domain="[('is_patient','=',True)]")
    appointment_id = fields.Many2one('dental.appointment', string='Appointment')
    dentist_id = fields.Many2one('hr.employee', string='Dentist',
        domain="[('is_dentist','=',True)]")
    consent_body = fields.Html(string='Consent Text',
        related='template_id.body', readonly=True)
    state = fields.Selection([
        ('pending', 'Pending Signature'),
        ('signed', 'Signed'),
        ('declined', 'Declined'),
    ], default='pending', tracking=True)
    signed_date = fields.Datetime(string='Signed On')
    signed_by = fields.Char(string='Signed By (Printed Name)')
    patient_signature = fields.Binary(string='Patient Signature')
    witness_name = fields.Char(string='Witness')
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'dental.consent.form') or '/'
        return super().create(vals_list)

    def action_sign(self):
        self.write({
            'state': 'signed',
            'signed_date': fields.Datetime.now(),
        })

    def action_decline(self):
        self.write({'state': 'declined'})