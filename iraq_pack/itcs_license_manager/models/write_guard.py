import logging

from odoo import models

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global read-only enforcement.
#
# When itcs_license.read_only == "1" (an ir.config_parameter, refreshed by
# itcs_license._refresh_read_only_flag() on every code application and once
# daily by the cron), all write/create/unlink calls are blocked EXCEPT for:
#   - the license models themselves (so an ITCS admin can still apply a
#     renewal code to get out of read-only mode)
#   - users in the ITCS admin group (group_itcs_license_admin)
#   - superuser context (SUPERUSER_ID, e.g. cron jobs, install/upgrade)
#
# This is a monkey-patch of models.BaseModel, which is the same technique
# Odoo's own built-in database-expiration mechanism uses. It is checked here
# via a single ir.config_parameter read (cached by the ORM's config
# parameter caching), not a per-write license lookup, to keep this cheap.
#
# Deliberately NOT touching read/search — clinics can always view and
# export their own data, even fully expired. Only mutation is blocked.
# This is the "read-only, never a hard lockout" principle agreed 2026-07-17.
# ---------------------------------------------------------------------------

_EXEMPT_MODELS = {
    "itcs.license",
    "itcs.license.renewal",
    "ir.config_parameter",
    "ir.cron",
    "ir.logging",
}

_orig_create = models.BaseModel.create
_orig_write = models.BaseModel.write
_orig_unlink = models.BaseModel.unlink


def _is_read_only(self):
    if self._name in _EXEMPT_MODELS:
        return False
    if self.env.su:
        return False
    if self.env.user.has_group("itcs_license_manager.group_itcs_license_admin"):
        return False
    return self.env["ir.config_parameter"].sudo().get_param("itcs_license.read_only") == "1"


def _guarded_create(self, *args, **kwargs):
    if _is_read_only(self):
        from odoo.exceptions import UserError
        raise UserError(
            "This system is currently in read-only mode (license/AMC "
            "expired). Your existing data is safe and fully viewable — "
            "please contact ITCS to renew access."
        )
    return _orig_create(self, *args, **kwargs)


def _guarded_write(self, *args, **kwargs):
    if _is_read_only(self):
        from odoo.exceptions import UserError
        raise UserError(
            "This system is currently in read-only mode (license/AMC "
            "expired). Your existing data is safe and fully viewable — "
            "please contact ITCS to renew access."
        )
    return _orig_write(self, *args, **kwargs)


def _guarded_unlink(self, *args, **kwargs):
    if _is_read_only(self):
        from odoo.exceptions import UserError
        raise UserError(
            "This system is currently in read-only mode (license/AMC "
            "expired). Your existing data is safe and fully viewable — "
            "please contact ITCS to renew access."
        )
    return _orig_unlink(self, *args, **kwargs)


models.BaseModel.create = _guarded_create
models.BaseModel.write = _guarded_write
models.BaseModel.unlink = _guarded_unlink

_logger.info("itcs_license_manager: write guard installed")
