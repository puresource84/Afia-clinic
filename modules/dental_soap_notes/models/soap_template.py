"""
dental.soap.template — reusable SOAP note skeletons per procedure type.
Templates now carry One2many sentence lists per SOAP section.
Selecting a template on a note pre-fills all four sections from the library.
"""
from odoo import fields, models


class DentalSoapTemplate(models.Model):
    _name = 'dental.soap.template'
    _description = 'SOAP Note Template'
    _order = 'name'

    name = fields.Char(string='Procedure / Template Name',
                       required=True, translate=True)
    category_id = fields.Many2one(
        'dental.treatment.category', string='Treatment Category',
        help='Optional: links this template to a treatment type.')
    active = fields.Boolean(default=True)

    # ── Header fields (pre-filled into the note header) ───────────────────────
    chief_complaint = fields.Char(
        string='Chief Complaint (default)',
        help='Pre-filled into the note Chief Complaint when template is applied.')
    cdt_codes = fields.Char(
        string='Default CDT / Procedure Codes',
        help='Comma-separated CDT codes pre-loaded when template is applied.')

    # ── Content library — sentences per SOAP section ──────────────────────────
    # One2many via template_id on dental.soap.sentence; domain filters by section.
    # From the template form, dentists can add/edit sentences per section tab.
    s_sentence_ids = fields.One2many(
        'dental.soap.sentence', 'template_id',
        string='Subjective Entries',
        domain=[('section', '=', 'S')])

    o_sentence_ids = fields.One2many(
        'dental.soap.sentence', 'template_id',
        string='Objective Entries',
        domain=[('section', '=', 'O')])

    a_sentence_ids = fields.One2many(
        'dental.soap.sentence', 'template_id',
        string='Assessment Entries',
        domain=[('section', '=', 'A')])

    p_sentence_ids = fields.One2many(
        'dental.soap.sentence', 'template_id',
        string='Plan Entries',
        domain=[('section', '=', 'P')])
