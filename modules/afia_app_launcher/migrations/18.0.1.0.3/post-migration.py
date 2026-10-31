# -*- coding: utf-8 -*-
"""Roll the branded launcher background out to databases that already exist.

post_init_hook only runs on install, and the seeding it calls refuses to
touch a background that is already configured — correct, since a clinic may
have uploaded its own. The effect was that every database installed before
this version kept the unbranded image with no way to receive a new one.

_seed_default_background(replace_shipped_default=True) resolves that by
identity rather than by date: it replaces the background only when the bytes
match one this module shipped, and leaves anything else alone.
"""
from odoo import api, SUPERUSER_ID

from odoo.addons.afia_app_launcher.hooks import _seed_default_background


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    _seed_default_background(env, replace_shipped_default=True)
