# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Set the Afia App Launcher as the home action for clinic staff only.

    Only targets users who belong to at least one clinic group
    (admin, dentist, receptionist, assistant).  Finance, HR, and other
    back-office users keep their standard Odoo home so that Purchase,
    Accounting, and Inventory URL routing is not contaminated.
    """
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
            'clinic_core.group_clinic_admin',
            'clinic_core.group_clinic_dentist',
            'clinic_core.group_clinic_receptionist',
            'clinic_core.group_clinic_assistant',
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
