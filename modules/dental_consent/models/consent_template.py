from odoo import models, fields


class DentalConsentTemplate(models.Model):
    _name = 'dental.consent.template'
    _description = 'Consent Form Template'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    procedure_type = fields.Char(string='Procedure Type')
    body = fields.Html(string='Consent Text', required=True)
    requires_signature = fields.Boolean(default=True)