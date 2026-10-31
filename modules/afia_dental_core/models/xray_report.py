# -*- coding: utf-8 -*-
"""X-Ray report attached to a patient. Clean-room rewrite (2026-08).

Schema reconstructed from the companion module dental_clinical_permissions,
which documents (in its own views/xray_report_views.xml) the exact fields
this core model must expose: patient_id, report_date, description,
scan_image, image_filename. That companion module ships its own standalone
form view (with chatter, once mail.thread is mixed in there) and expects
core NOT to register a competing primary form view — deliberately left
unregistered here for the same reason. We ship this as a plain model (not
a wizard — X-ray reports are patient records that must persist, never
Transient).
"""
from odoo import fields, models


class XRayReport(models.Model):
    _name = 'xray.report'
    _description = 'X-Ray Report'
    _order = 'report_date desc'

    patient_id = fields.Many2one(
        'res.partner', string='Patient', required=True, ondelete='cascade',
        domain="[('is_patient', '=', True)]")
    report_date = fields.Date(default=fields.Date.context_today, required=True)
    description = fields.Char()
    scan_image = fields.Binary(string='Scan Image', attachment=True)
    image_filename = fields.Char(string='Filename')
