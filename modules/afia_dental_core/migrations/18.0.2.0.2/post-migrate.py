# -*- coding: utf-8 -*-
"""Superseded 2026-08-16 — left as a harmless no-op.

The default_duration field this migration used to backfill turned out to
already be owned by dental_appointment_times (see that module's own
migrations/18.0.1.0.1/post-migrate.py for the real fix). Declaring the
same field name here too silently merged into one DB column but shadowed
dental_appointment_times' onchange and duplicated a list-view column —
see project_afia_click_everywhere_qa_2026-08-15 memory. This version
number already ran once before the fix, so Odoo won't re-run it; the file
is kept (rather than deleted) only because a Windows file lock on this
addons path from this environment prevented an actual delete.
"""


def migrate(cr, version):
    pass
