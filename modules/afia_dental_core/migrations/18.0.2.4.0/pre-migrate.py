"""Merge the duplicate clinic roles into the single canonical set.

Afia used to ship two parallel role hierarchies. This moves every user who
holds a retired role onto its replacement, BEFORE the retired group records
are removed by the module update - otherwise those users silently lose all
their clinic permissions.

Runs on an existing database only (version is falsy on a fresh install).
"""
import logging

_logger = logging.getLogger(__name__)

MERGE = [
    ("group_dental_manager", "group_clinic_admin"),
    ("group_dental_dentist", "group_clinic_dentist"),
    ("group_dental_reception", "group_clinic_receptionist"),
]


def _gid(cr, name):
    cr.execute("""
        SELECT res_id FROM ir_model_data
         WHERE module = 'afia_dental_core' AND name = %s AND model = 'res.groups'
    """, (name,))
    row = cr.fetchone()
    return row[0] if row else None


def migrate(cr, version):
    if not version:
        return
    for old_name, new_name in MERGE:
        old_id, new_id = _gid(cr, old_name), _gid(cr, new_name)
        if not old_id or not new_id:
            continue
        cr.execute("""
            INSERT INTO res_groups_users_rel (gid, uid)
            SELECT %s, uid FROM res_groups_users_rel WHERE gid = %s
            ON CONFLICT DO NOTHING
        """, (new_id, old_id))
        moved = cr.rowcount
        if moved:
            _logger.info("Merged %s user(s) from %s into %s", moved, old_name, new_name)
