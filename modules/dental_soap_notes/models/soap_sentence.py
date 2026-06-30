"""
dental.soap.sentence — reusable SOAP content library.
Each entry is a single clinical phrase / sentence for one SOAP section.
Dentists select entries via autocomplete (many2many_tags) on the note form;
new phrases typed inline are saved back to the library so the list grows
organically over time.

Odoo 18 notes:
- _order avoids Many2one columns (use section/sequence instead)
- display_name computed (Odoo 18 style, replaces name_get)
- No _name_search override needed; _rec_name='text' gives text-based search
"""
from odoo import api, fields, models


class DentalSoapSentence(models.Model):
    _name = 'dental.soap.sentence'
    _description = 'SOAP Content Library Entry'
    _order = 'section, sequence, id'
    _rec_name = 'text'

    section = fields.Selection([
        ('S', 'Subjective'),
        ('O', 'Objective'),
        ('A', 'Assessment'),
        ('P', 'Plan'),
    ], required=True, string='SOAP Section', index=True)

    template_id = fields.Many2one(
        'dental.soap.template', string='Template Category',
        ondelete='set null', index=True,
        help='Categorize this entry under a procedure template (optional).')

    text = fields.Text(string='Content', required=True,
        help='A single clinical phrase or sentence for this SOAP section.')

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    # Odoo 18: use _compute_display_name instead of name_get
    display_name = fields.Char(
        compute='_compute_display_name', store=False)

    @api.depends('text')
    def _compute_display_name(self):
        for rec in self:
            label = (rec.text or '')[:80]
            if len(rec.text or '') > 80:
                label += '…'
            rec.display_name = label
