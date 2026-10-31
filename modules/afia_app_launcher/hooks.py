# -*- coding: utf-8 -*-
import base64
import binascii
import hashlib
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

# Key recording the sha256 of whatever bundled default this module last
# seeded. It is what makes an upgrade able to tell "the image we shipped"
# from "the image this clinic uploaded", so a new default can roll out
# without ever overwriting a clinic's own artwork. See _seed_default_background.
_BG_SHA_PARAM = 'afia_launcher.bg_default_sha'

# sha256 of every background this module has ever shipped. Needed because
# the seeding hook predates _BG_SHA_PARAM: on a database seeded by the old
# hook there is no recorded sha, and without this list the unbranded image
# those installs are still showing would be mistaken for a clinic upload and
# left in place forever. Append, never remove.
_SHIPPED_DEFAULT_SHAS = {
    # Unbranded dental background, shipped until 18.0.1.0.4.
    'cbbdeab419e244c1851b15da649a0faf979f4f2797e38e6aa3e24147872119ec',
}


def _read_bundled_default():
    """Return (base64_str, sha256_hex) of the bundled background, or (None, None)."""
    # hooks.py lives at the module root, so ONE dirname reaches the module
    # directory. This took dirname twice until 18.0.1.0.4 and so pointed at
    # the addons directory, where the image will never be; the read failed on
    # every install, the warning below went unread, and no clinic ever got a
    # launcher background. Hence the error level: a default that silently
    # does not arrive looks exactly like a feature that was removed.
    module_path = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(module_path, _DEFAULT_BG_RELPATH)
    try:
        with open(image_path, 'rb') as f:
            raw = f.read()
    except OSError:
        _logger.error(
            'afia_app_launcher: bundled default background missing at %s — '
            'the launcher will have no background.', image_path,
        )
        return None, None
    return base64.b64encode(raw).decode('ascii'), hashlib.sha256(raw).hexdigest()


def _current_bg_sha(current_b64):
    """sha256 of the background currently configured, or None if unreadable."""
    try:
        return hashlib.sha256(base64.b64decode(current_b64)).hexdigest()
    except (binascii.Error, ValueError, TypeError):
        return None


def _seed_default_background(env, replace_shipped_default=False):
    """Install the bundled background.

    Never clobbers a clinic's own upload. With replace_shipped_default the
    bundled image also supersedes an older bundled one — that is the upgrade
    path, and it is why the sha is recorded on every write.
    """
    ICP = env['ir.config_parameter'].sudo()
    current = ICP.get_param('afia_launcher.bg_image')

    if current and not replace_shipped_default:
        return  # already configured (either by us before, or by an admin)

    if current:
        known = set(_SHIPPED_DEFAULT_SHAS)
        recorded = ICP.get_param(_BG_SHA_PARAM)
        if recorded:
            known.add(recorded)
        if _current_bg_sha(current) not in known:
            _logger.info(
                'afia_app_launcher: launcher background is not one this module '
                'shipped, leaving the clinic\'s own image in place.'
            )
            return

    b64, sha = _read_bundled_default()
    if not b64:
        return

    ICP.set_param('afia_launcher.bg_image', b64)
    ICP.set_param(_BG_SHA_PARAM, sha)
    if not ICP.get_param('afia_launcher.bg_opacity'):
        ICP.set_param('afia_launcher.bg_opacity', _DEFAULT_BG_OPACITY)
    _logger.info('afia_app_launcher: seeded default launcher background.')


def post_init_hook(env):
    """Set the Afia App Launcher as the home action for clinic staff only.

    Only targets users who belong to at least one clinic group
    (admin, dentist, hygienist, receptionist).  Finance, HR, and other
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
            'afia_dental_core.group_clinic_hygienist',
            'afia_dental_core.group_clinic_receptionist',
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
