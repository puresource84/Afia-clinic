from odoo import fields, models
from odoo.exceptions import UserError


class ItcsLicenseApplyCodeWizard(models.TransientModel):
    _name = "itcs.license.apply.code.wizard"
    _description = "Apply ITCS License Renewal Code (internal)"

    license_id = fields.Many2one("itcs.license", required=True)
    code = fields.Char(required=True, help="Paste the AFIA-... renewal code here.")

    def action_apply(self):
        self.ensure_one()
        if not self.code:
            raise UserError("Enter a renewal code first.")
        self.license_id.action_apply_renewal_code(self.code)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "License renewed",
                "message": "New expiry date: %s" % self.license_id.expiry_date,
                "type": "success",
                "sticky": False,
            },
        }
