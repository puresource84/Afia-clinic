# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class AfiaLauncherBranding(http.Controller):

    @http.route('/afia_launcher/branding', type='json', auth='user')
    def get_branding(self):
        """Return launcher background image (base64) and opacity from ir.config_parameter."""
        ICP = request.env['ir.config_parameter'].sudo()
        bg_image = ICP.get_param('afia_launcher.bg_image', False)
        try:
            bg_opacity = float(ICP.get_param('afia_launcher.bg_opacity', '0.6'))
        except (TypeError, ValueError):
            bg_opacity = 0.6
        # Clamp opacity to a sensible range
        bg_opacity = max(0.1, min(1.0, bg_opacity))
        return {
            'bg_image': bg_image or False,
            'bg_opacity': bg_opacity,
        }
