# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AfiaLauncherBranding(models.TransientModel):
    """
    Wizard for white-label launcher config.
    Opens as a popup dialog (target=new). Values are persisted in
    ir.config_parameter so they survive upgrades and apply to all users.
    """
    _name = 'afia.launcher.branding'
    _description = 'Afia Launcher Branding'

    bg_image = fields.Binary(
        string='Background Image',
        help=(
            'Upload a logo or pattern for the app launcher page. '
            'PNG with a transparent background works best. '
            'Recommended size: 800 x 600 px or larger.'
        ),
    )
    bg_opacity = fields.Float(
        string='Opacity',
        default=0.6,
        help='How strongly the image shows through (0.0 = hidden, 1.0 = solid). Recommended: 0.50 – 0.80.',
    )

    # ---------------------------------------------------------------- lifecycle

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ICP = self.env['ir.config_parameter'].sudo()
        if 'bg_image' in fields_list:
            val = ICP.get_param('afia_launcher.bg_image', False)
            res['bg_image'] = val if val else False
        if 'bg_opacity' in fields_list:
            try:
                res['bg_opacity'] = float(ICP.get_param('afia_launcher.bg_opacity', '0.6'))
            except (TypeError, ValueError):
                res['bg_opacity'] = 0.6
        return res

    # ---------------------------------------------------------------- actions

    def action_save(self):
        ICP = self.env['ir.config_parameter'].sudo()

        # Binary fields may return bytes in Odoo 18 — decode to plain string
        bg_image = self.bg_image or b''
        if isinstance(bg_image, bytes):
            bg_image = bg_image.decode('ascii')

        ICP.set_param('afia_launcher.bg_image', bg_image)
        ICP.set_param('afia_launcher.bg_opacity',
                      str(max(0.1, min(1.0, self.bg_opacity or 0.6))))

        # Close dialog and show a success toast
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Saved',
                'message': 'Launcher branding updated. Reload the launcher page to see the change.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_clear_image(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'afia_launcher.bg_image', '')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Cleared',
                'message': 'Background image removed.',
                'type': 'info',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
