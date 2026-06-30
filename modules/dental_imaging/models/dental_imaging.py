"""
A6 v1 — Dental Imaging (attachment-based).

Adds a Many2many ir.attachment gallery to:
  • dental.tooth.record  (per-tooth images / X-rays)
  • dental.appointment   (per-visit images / intraoral camera shots)

No DICOM processing — any image format the browser renders is fine for v1.
DICOM import can be layered on top in v2 using pydicom.
"""
from odoo import fields, models


class DentalToothRecordImaging(models.Model):
    _inherit = 'dental.tooth.record'

    image_ids = fields.Many2many(
        'ir.attachment',
        'dental_tooth_image_rel',
        'tooth_record_id',
        'attachment_id',
        string='Images / X-rays',
        domain="[('mimetype', 'like', 'image/')]",
    )
    image_count = fields.Integer(
        compute='_compute_image_count', string='Images')

    def _compute_image_count(self):
        for rec in self:
            rec.image_count = len(rec.image_ids)


class DentalAppointmentImaging(models.Model):
    _inherit = 'dental.appointment'

    visit_image_ids = fields.Many2many(
        'ir.attachment',
        'dental_appt_image_rel',
        'appointment_id',
        'attachment_id',
        string='Visit Images',
        domain="[('mimetype', 'like', 'image/')]",
    )
    visit_image_count = fields.Integer(
        compute='_compute_visit_image_count', string='Images')

    def _compute_visit_image_count(self):
        for rec in self:
            rec.visit_image_count = len(rec.visit_image_ids)

    def action_open_visit_images(self):
        """Open the Visit Images page (scrolls to the notebook tab via form view)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dental.appointment',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'context': {'active_id': self.id},
        }
