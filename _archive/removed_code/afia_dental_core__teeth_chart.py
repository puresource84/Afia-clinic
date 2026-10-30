# -*- coding: utf-8 -*-
"""Removed 2026-08-15.

The legacy flat tooth chart (teeth.chart, one boolean per tooth) has been
fully superseded by dental_charting_pro's proper FDI odontogram
(dental.tooth.record). Zero real teeth.chart records existed on db_odoo at
removal time. Model intentionally left empty/unimported (see
models/__init__.py) rather than deleted outright — Windows file locks on
this addons path while the Odoo service is running block a real delete
from this environment. Do not reintroduce without checking with Manhel
first; see project_afia_click_everywhere_qa_2026-08-15 memory.
"""
