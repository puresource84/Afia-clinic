"""Re-point security groups moved into afia_dental_core on 2026-10-30.

group_dental_clinician came from dental_charting, group_clinic_hygienist from
dental_clinical_permissions. Without this, upgrading an existing database would
leave the old ir.model.data rows orphaned and create duplicate empty groups,
silently dropping every user's membership.
"""
import logging
_logger = logging.getLogger(__name__)

MOVED = [
    ("dental_charting", "group_dental_clinician"),
    ("dental_clinical_permissions", "group_clinic_hygienist"),
]


def migrate(cr, version):
    if not version:
        return
    for old_module, name in MOVED:
        cr.execute("""
            UPDATE ir_model_data
               SET module = %s
             WHERE module = %s AND name = %s AND model = 'res.groups'
        """, ("afia_dental_core", old_module, name))
        if cr.rowcount:
            _logger.info("Moved group xmlid %s.%s -> afia_dental_core.%s",
                         old_module, name, name)
