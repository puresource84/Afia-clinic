# -*- coding: utf-8 -*-
"""Backfill dental.treatment.default_duration with real values (2026-08-16).

This module has always owned default_duration (see models/appointment_times.py
— its onchange fills apt_duration/apt_end_time from it), but it shipped with
default=0.0 and no seed data, so every treatment showed 00:00 until someone
opened each record and typed a value in by hand — this is exactly the gap
flagged in project_afia_click_everywhere_qa_2026-08-15.

Matched by afia_dental_core's treatment external IDs (this module depends on
afia_dental_core so those xmlids are guaranteed to resolve once it's
installed). Safe to re-run: only touches records still at the 0.0 default,
so it won't clobber a value a clinic has since customized.
"""
import logging

_logger = logging.getLogger(__name__)

DEFAULTS = {
    'afia_dental_core.treatment_checkup': 0.25,     # Routine Check-up — 15 min
    'afia_dental_core.treatment_cleaning': 0.5,      # Scaling & Polishing — 30 min
    'afia_dental_core.treatment_filling': 0.75,      # Composite Filling — 45 min
    'afia_dental_core.treatment_rootcanal': 1.5,     # Root Canal Treatment — 90 min
    'afia_dental_core.treatment_extraction': 0.5,    # Tooth Extraction — 30 min
    'afia_dental_core.treatment_whitening': 1.0,     # Teeth Whitening — 60 min
}


def migrate(cr, version):
    env = _get_env(cr)
    for xmlid, hours in DEFAULTS.items():
        treatment = env.ref(xmlid, raise_if_not_found=False)
        if not treatment:
            _logger.info('Migration skip: %s not found (custom DB layout).', xmlid)
            continue
        if not treatment.default_duration:
            treatment.default_duration = hours


def _get_env(cr):
    from odoo import api, SUPERUSER_ID
    return api.Environment(cr, SUPERUSER_ID, {})
