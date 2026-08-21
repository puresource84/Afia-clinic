import logging

_logger = logging.getLogger(__name__)

# Same (model_xmlid, field -> value) overrides as security/access_overrides.xml.
# Kept here as plain data so the hook can re-apply them programmatically —
# see post_init_hook() below for why this needs to run outside of pure XML data.
ACCESS_OVERRIDES = [
    ('afia_dental_core.access_dental_prescription',
     {'perm_write': False, 'perm_create': False, 'perm_unlink': False}),
    ('afia_dental_core.access_dental_prescription_lines',
     {'perm_write': False, 'perm_create': False, 'perm_unlink': False}),
    ('afia_dental_core.access_medical_questionnaire',
     {'perm_write': False, 'perm_create': False, 'perm_unlink': False}),
    ('afia_dental_core.access_xray_report',
     {'perm_read': False, 'perm_write': False, 'perm_create': False, 'perm_unlink': False}),
    ('afia_dental_core.access_dental_treatment',
     {'perm_write': False, 'perm_create': False, 'perm_unlink': False}),
    ('afia_dental_core.access_treatment_category',
     {'perm_write': False, 'perm_create': False, 'perm_unlink': False}),
    ('dental_treatment_plan.access_plan',
     {'perm_write': False, 'perm_create': False, 'perm_unlink': False}),
    ('dental_treatment_plan.access_plan_line',
     {'perm_write': False, 'perm_create': False, 'perm_unlink': False}),
    ('dental_consent.access_consent_tmpl',
     {'perm_write': False, 'perm_create': False, 'perm_unlink': False}),
    ('dental_consent.access_consent_form',
     {'perm_unlink': False}),
]


def reapply_access_overrides(env):
    """Re-apply the ACL tightening from security/access_overrides.xml.

    afia_dental_core / dental_treatment_plan / dental_consent each ship their
    own ir.model.access.csv granting full CRUD to base.group_user. This
    module's access_overrides.xml demotes those specific rows to match the
    role matrix. The problem: upgrading any of those THREE source modules
    reloads their CSV and resets the demoted rows back to 1,1,1,1 — silently
    re-opening write/unlink access to unauthenticated internal roles until
    someone remembers to re-upgrade dental_clinical_permissions by hand.

    This function is the self-healing half of that fix: it re-applies the
    same overrides in Python, so it can be invoked from a post_init_hook
    (this module's own installs/upgrades) AND wired as a post_init_hook on
    the three source modules themselves is not possible without editing
    their manifests — instead, we call this from THIS module's post_init_hook
    for install/upgrade of dental_clinical_permissions, and document (see
    access_overrides.xml + README) that re-upgrading this module after
    touching the other three remains the trigger. The hook removes the
    "forgot the exact field values" failure mode; it does not remove the
    "forgot to click upgrade" failure mode, which would require a
    cross-module hook Odoo does not support cleanly.
    """
    Access = env['ir.model.access']
    updated = skipped = 0
    for xmlid, vals in ACCESS_OVERRIDES:
        access = env.ref(xmlid, raise_if_not_found=False)
        if not access:
            _logger.warning('access_overrides: xmlid %s not found — skipped.', xmlid)
            skipped += 1
            continue
        diff = {k: v for k, v in vals.items() if getattr(access, k) != v}
        if diff:
            access.write(diff)
            updated += 1
    _logger.info(
        'dental_clinical_permissions: re-applied ACL overrides (%d changed, %d skipped).',
        updated, skipped)


def post_init_hook(env):
    reapply_access_overrides(env)
