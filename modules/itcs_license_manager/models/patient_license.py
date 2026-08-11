from odoo import api, fields, models


class ResPartnerLicense(models.Model):
    """Active-patient capacity check + availability banner. Patient
    inactivation is staff-reviewed only (see afia_dental_core's own
    inactivity flow, if present) — this module never archives a patient
    on its own; it only warns/blocks new active patients past the plan's
    buffer."""
    _inherit = "res.partner"

    afia_patient_banner_type = fields.Char(compute="_compute_afia_patient_banner")
    afia_patient_banner_text = fields.Char(compute="_compute_afia_patient_banner")

    @api.depends_context("uid")
    def _compute_afia_patient_banner(self):
        license_rec = self.env["itcs.license"].sudo().get_active_license()
        for rec in self:
            if not license_rec or not rec.is_patient:
                rec.afia_patient_banner_type = "none"
                rec.afia_patient_banner_text = ""
                continue
            info = license_rec._afia_banner_info("patient")
            rec.afia_patient_banner_type = info["type"]
            rec.afia_patient_banner_text = info["text"]

    def _afia_check_patient_cap(self):
        license_rec = self.env["itcs.license"].sudo().get_active_license()
        if not license_rec:
            return
        count = self.env["res.partner"].sudo().search_count([("is_patient", "=", True)])
        license_rec._afia_check_cap("patient", count)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if any(v.get("is_patient") for v in vals_list):
            records._afia_check_patient_cap()
        return records

    def write(self, vals):
        result = super().write(vals)
        if "is_patient" in vals or "active" in vals:
            self._afia_check_patient_cap()
        return result
