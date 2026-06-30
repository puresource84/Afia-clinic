"""
B2 — Clinical Audit Trail
=========================
Redefines key fields on clinical models with ``tracking=True`` so every
change appears in the chatter.  No new fields are added; no views or ACLs
are needed.  This module has no effect on existing data — tracking begins
from the moment it is installed.

Tracking priority numbers are kept low (1–9) to avoid collisions with any
future upstream additions.
"""
from markupsafe import Markup, escape

from odoo import api, fields, models


# ─── Appointment ─────────────────────────────────────────────────────────────

class DentalAppointmentAudit(models.Model):
    _inherit = 'dental.appointment'

    # state already has tracking=True in dental_hospital — leave it.
    patient_id = fields.Many2one(tracking=1)
    dentist_id = fields.Many2one(tracking=2)
    appointment_date = fields.Date(tracking=3)
    urgency = fields.Selection(tracking=4)
    shift_id = fields.Many2one(tracking=5)


# ─── Prescription ─────────────────────────────────────────────────────────────

class DentalPrescriptionAudit(models.Model):
    _inherit = 'dental.prescription'

    state = fields.Selection(tracking=1)
    referred_dentist_id = fields.Many2one(tracking=2)
    next_appointment_date = fields.Date(tracking=3)


# ─── Treatment plan ───────────────────────────────────────────────────────────

class DentalTreatmentPlanAudit(models.Model):
    _inherit = 'dental.treatment.plan'

    # state already has tracking=True in dental_treatment_plan — leave it.
    patient_id = fields.Many2one(tracking=1)
    dentist_id = fields.Many2one(tracking=2)
    diagnosis = fields.Text(tracking=3)


# ─── Treatment plan line ──────────────────────────────────────────────────────

class DentalTreatmentPlanLineAudit(models.Model):
    _inherit = 'dental.treatment.plan.line'

    state = fields.Selection(tracking=1)
    appointment_id = fields.Many2one(tracking=2)
    scheduled_date = fields.Date(tracking=3)


# ─── Consent form ─────────────────────────────────────────────────────────────

class DentalConsentFormAudit(models.Model):
    _inherit = 'dental.consent.form'

    # state already has tracking=True in dental_consent — leave it.
    signed_by = fields.Char(tracking=1)
    signed_date = fields.Datetime(tracking=2)
    witness_name = fields.Char(tracking=3)
    dentist_id = fields.Many2one(tracking=4)


# ─── Tooth record ─────────────────────────────────────────────────────────────

class DentalToothRecordAudit(models.Model):
    _inherit = 'dental.tooth.record'

    # condition already has tracking=True in dental_charting_pro — leave it.
    doctor_id = fields.Many2one(tracking=2)
    is_current = fields.Boolean(tracking=3)
    notes = fields.Text(tracking=4)


# ─── Patient (res.partner) — free-text allergy alert ─────────────────────────

class ResPartnerAudit(models.Model):
    _inherit = 'res.partner'

    # allergy_alert already has tracking=True in dental_ux_fixes — reinforcing.
    allergy_alert = fields.Text(tracking=1)


# ─── Structured allergy list — log add/edit/remove to patient chatter ─────────

class DentalPatientAllergyAudit(models.Model):
    """
    dental.patient.allergy doesn't inherit mail.thread, so changes to the
    structured allergy list (substance, severity, reaction) are invisible.
    These create/write/unlink overrides post an audit note to the parent
    patient (res.partner) chatter instead.
    """
    _inherit = 'dental.patient.allergy'

    def _sev_label(self, key):
        return dict(self._fields['severity'].selection).get(key, key)

    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            body = (
                Markup("⚠ <b>Allergy added:</b> %s — severity: %s")
                % (escape(rec.substance_id.name),
                   escape(self._sev_label(rec.severity)))
            )
            if rec.reaction:
                body += Markup(", reaction: %s") % escape(rec.reaction)
            rec.partner_id.message_post(body=body)
        return records

    def write(self, vals):
        # Capture before-state while records are still accessible
        before = {
            r.id: {
                'substance': r.substance_id.name,
                'severity': r.severity,
                'reaction': r.reaction or '',
            }
            for r in self
        }
        res = super().write(vals)
        for rec in self:
            b = before[rec.id]
            changes = []
            if rec.substance_id.name != b['substance']:
                changes.append(
                    Markup("Substance: %s → %s")
                    % (escape(b['substance']), escape(rec.substance_id.name))
                )
            if rec.severity != b['severity']:
                changes.append(
                    Markup("Severity: %s → %s")
                    % (escape(self._sev_label(b['severity'])),
                       escape(self._sev_label(rec.severity)))
                )
            cur_reaction = rec.reaction or ''
            if cur_reaction != b['reaction']:
                changes.append(
                    Markup("Reaction: %s → %s")
                    % (escape(b['reaction'] or '(none)'),
                       escape(cur_reaction or '(none)'))
                )
            if changes:
                body = (
                    Markup("⚠ <b>Allergy updated</b> (%s): ")
                    % escape(rec.substance_id.name)
                ) + Markup(', ').join(changes)
                rec.partner_id.message_post(body=body)
        return res

    def unlink(self):
        # Capture before deletion
        to_log = [(r.partner_id, r.substance_id.name) for r in self]
        res = super().unlink()
        for partner, name in to_log:
            partner.message_post(
                body=Markup("⚠ <b>Allergy removed:</b> %s") % escape(name)
            )
        return res
