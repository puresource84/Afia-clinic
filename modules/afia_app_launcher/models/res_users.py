# -*- coding: utf-8 -*-
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-set the App Launcher as home action for new internal users."""
        users = super().create(vals_list)
        launcher = self.env['ir.actions.client'].search(
            [('tag', '=', 'afia_app_launcher')], limit=1
        )
        if launcher:
            internal = users.filtered(lambda u: not u.share)
            if internal:
                internal.write({'action_id': launcher.id})
        return users
