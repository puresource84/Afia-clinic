# -*- coding: utf-8 -*-
import base64
import logging
import os

_logger = logging.getLogger(__name__)

# Bundled default background — every fresh Afia Clinic install gets this
# out of the box so the launcher never looks "bare". Config-parameter based
# (ir.config_parameter is DB-wide, not per-user), so it applies to every
# user and group automatically, with no per-user setup step. Clinic admins
# can still replace it any time via Afia Clinic > Configuration > Launcher
# Branding — action_save() there simply overwrites the same two keys.
_DEFAULT_BG_RELPATH = os.path.join(
    'static', 'src', 'img', 'default_launcher_bg.jpg'
)
_DEFAULT_BG_OPACITY = '0.6'


def _seed_default_background(env):
    """Populate afia_launcher.bg_image with the bundled default, but only
    if no image is configured yet — never clobber an admin's own upload
    on a module upgrade/reinstall."""
    ICP = env['ir.config_parameter'].sudo()
    if ICP.get_param('afia_launcher.bg_image'):
        return  # already configured (either by us before, or by an admin)

    module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_path = os.path.join(module_path, _DEFAULT_BG_RELPATH)
    try:
        with open(image_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
    except OSError:
        _logger.warning(
            'afia_app_launcher: bundled default background not found at %s, '
            'skipping.', image_path,
        )
        return

    ICP.set_param('afia_launcher.bg_image', b64)
    ICP.set_param('afia_launcher.bg_opacity', _DEFAULT_BG_OPACITY)
    _logger.info('afia_app_launcher: seeded default launcher background.')


def post_init_hook(env):
    """Set the Afia App Launcher as the home action for clinic staff only.

    Only targets users who belong to at least one clinic group
    (admin, dentist, receptionist, assistant).  Finance, HR, and other
    back-office users keep their standard Odoo home so that Purchase,
    Accounting, and Inventory URL routing is not contaminated.
    """
    _seed_default_background(env)

    launcher = env['ir.actions.client'].search(
        [('tag', '=', 'afia_app_launcher')], limit=1
    )
    if not launcher:
        _logger.warning(
            'afia_app_launcher: client action not found, skipping home action setup.'
        )
        return

    # Resolve clinic group XML IDs — fail silently if clinic_core not ready yet
    try:
        clinic_group_refs = [
            'afia_dental_core.group_clinic_admin',
            'afia_dental_core.group_clinic_dentist',
            'afia_dental_core.group_clinic_receptionist',
            'afia_dental_core.group_clinic_assistant',
        ]
        group_ids = []
        for ref in clinic_group_refs:
            try:
                group_ids.append(env.ref(ref).id)
            except ValueError:
                pass  # group not installed yet — skip

        if not group_ids:
            _logger.warning(
                'afia_app_launcher: no clinic groups found; '
                'home action NOT applied to any user.'
            )
            return

        clinic_users = env['res.users'].search([
            ('share', '=', False),
            ('active', '=', True),
            ('groups_id', 'in', group_ids),
        ])
        clinic_users.write({'action_id': launcher.id})
        _logger.info(
            'afia_app_launcher: set as home action for %d clinic user(s).',
            len(clinic_users),
        )
    except Exception:
        _logger.exception('afia_app_launcher: post_init_hook failed unexpectedly.')
