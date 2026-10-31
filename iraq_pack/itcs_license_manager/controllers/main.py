from markupsafe import Markup, escape

from odoo import http
from odoo.http import request


class ItcsLicenseBannerController(http.Controller):

    def _banner_html(self, kind):
        license_rec = request.env["itcs.license"].sudo().get_active_license()
        if not license_rec:
            return ""
        info = license_rec._afia_banner_info(kind)
        if info["type"] == "none" or not info["text"]:
            return ""
        css_class = {
            "ok": "alert-success",
            "warning": "alert-warning",
            "danger": "alert-danger",
        }.get(info["type"], "alert-info")
        return Markup(
            '<div class="alert %s mb-0 mx-3 mt-2" role="alert">%s</div>'
        ) % (css_class, escape(info["text"]))

    @http.route("/itcs_license/patients_banner", type="http", auth="user")
    def patients_banner(self, **kwargs):
        return self._banner_html("patient")

    @http.route("/itcs_license/staff_banner", type="http", auth="user")
    def staff_banner(self, **kwargs):
        return self._banner_html("dentist")
