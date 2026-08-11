from markupsafe import Markup, escape

from odoo import http
from odoo.http import request


class ItcsLicenseBannerController(http.Controller):

    @http.route("/itcs_license/patients_banner", type="http", auth="user")
    def patients_banner(self, **kwargs):
        license_rec = request.env["itcs.license"].sudo().get_active_license()
        if not license_rec:
            return ""
        info = license_rec._afia_banner_info("patient")
        if info["type"] == "none" or not info["text"]:
            return ""
        css_class = {
            "ok": "alert-success",
            "warning": "alert-warning",
            "danger": "alert-danger",
        }.get(info["type"], "alert-info")
        html = Markup(
            '<div class="alert %s mb-0" role="alert">%s</div>'
        ) % (css_class, escape(info["text"]))
        return html
