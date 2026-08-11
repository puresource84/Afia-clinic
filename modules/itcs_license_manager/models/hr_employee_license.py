from odoo import api, fields, models


class HrEmployeeLicense(models.Model):
    """Active-dentist capacity check + availability banner. Dentists are
    NEVER auto-inactivated by this module — archiving is always a manual
    HR action. See itcs_license.py for the cap logic itself."""
    _inherit = "hr.employee"

    afia_dentist_banner_type = fields.Char(compute="_compute_afia_dentist_banner")
    afia_dentist_banner_text = fields.Char(compute="_compute_afia_dentist_banner")

    @api.depends_context("uid")
    def _compute_afia_dentist_banner(self):
        license_rec = self.env["itcs.license"].sudo().get_active_license()
        for rec in self:
            if not license_rec:
                rec.afia_dentist_banner_type = "none"
                rec.afia_dentist_banner_text = ""
                continue
            info = license_rec._afia_banner_info("dentist")
            rec.afia_dentist_banner_type = info["type"]
            rec.afia_dentist_banner_text = info["text"]

    def _afia_check_dentist_cap(self):
        license_rec = self.env["itcs.license"].sudo().get_active_license()
        if not license_rec:
            return
        count = self.env["hr.employee"].sudo().search_count([("is_dentist", "=", True)])
        license_rec._afia_check_cap("dentist", count)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if any(v.get("is_dentist") for v in vals_list):
            records._afia_check_dentist_cap()
        return records

    def write(self, vals):
        result = super().write(vals)
        if "is_dentist" in vals or "active" in vals:
            self._afia_check_dentist_cap()
        return result
