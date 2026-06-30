# -*- coding: utf-8 -*-
"""
Sprint A data cleanup migration — runs once when dental_demo_data is
upgraded from 18.0.1.0.0 → 18.0.1.1.0.

Fixes:
  1. Set commission_pct = 15 % on all dentists currently at 0 %
  2. Upsert IQD exchange rate to ~1 310 IQD / 1 USD (current market rate)
  3. Delete the blank 00:00-00:00 dental.time.shift artifact
  4. Archive QA / test patients that have no real appointments
  5. Archive "Demo Dentist" test employee records
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})

    # ── 1. Dentist commission % ───────────────────────────────────────────
    dentists_no_commission = env['hr.employee'].search([
        ('is_dentist', '=', True),
        ('commission_pct', '=', 0.0),
    ])
    if dentists_no_commission:
        dentists_no_commission.write({'commission_pct': 15.0})
        _logger.info(
            'sprint_a_migration: set commission_pct=15 on %d dentist(s): %s',
            len(dentists_no_commission),
            ', '.join(dentists_no_commission.mapped('name')),
        )

    # ── 2. IQD exchange rate ─────────────────────────────────────────────
    # Rate field in res.currency.rate stores the inverse: rate = 1/X
    # where X is units of foreign currency per 1 company currency (USD).
    # IQD: 1 USD = 1 310 IQD → rate = 1/1310.
    iqd = env['res.currency'].search([('name', '=', 'IQD')], limit=1)
    if iqd:
        target_rate = 1.0 / 1310.0
        # Try to update the most-recent existing rate row
        existing = env['res.currency.rate'].search(
            [('currency_id', '=', iqd.id),
             ('company_id', '=', env.company.id)],
            order='name desc',
            limit=1,
        )
        if existing:
            existing.write({'rate': target_rate})
            _logger.info('sprint_a_migration: updated IQD rate to 1/1310 (row %s)', existing.name)
        else:
            env['res.currency.rate'].create({
                'currency_id': iqd.id,
                'name': '2025-01-01',
                'rate': target_rate,
                'company_id': env.company.id,
            })
            _logger.info('sprint_a_migration: created IQD rate row at 1/1310')
    else:
        _logger.warning('sprint_a_migration: IQD currency not found, rate not updated')

    # ── 3. Blank shift artifact ──────────────────────────────────────────
    # dental.time.shift.create() fires before start/end are populated,
    # leaving a record where both fields = 0.0 (shown as "00:00 – 00:00").
    blank_shifts = env['dental.time.shift'].search([
        ('shift_start', '=', 0.0),
        ('shift_end', '=', 0.0),
    ])
    if blank_shifts:
        count = len(blank_shifts)
        blank_shifts.unlink()
        _logger.info('sprint_a_migration: deleted %d blank 00:00-00:00 shift(s)', count)

    # ── 4. Archive QA / test patients with no appointments ───────────────
    qa_patterns = ['QA Patient', 'Test Patient', 'Demo Patient', 'Patient Test']
    domain = [('is_patient', '=', True)]
    domain += ['|'] * (len(qa_patterns) - 1)
    for p in qa_patterns:
        domain.append(('name', 'ilike', p))

    test_patients = env['res.partner'].search(domain)
    # Safety guard: only archive if no appointment records exist
    safe_to_archive = test_patients.filtered(
        lambda p: not env['dental.appointment'].search(
            [('patient_id', '=', p.id)], limit=1
        )
    )
    if safe_to_archive:
        safe_to_archive.write({'active': False})
        _logger.info(
            'sprint_a_migration: archived %d QA test patient(s): %s',
            len(safe_to_archive),
            ', '.join(safe_to_archive.mapped('name')),
        )

    # ── 5. Archive "Demo Dentist" test employee records ──────────────────
    demo_dentists = env['hr.employee'].search([('name', 'ilike', 'Demo Dentist')])
    if demo_dentists:
        demo_dentists.write({'active': False})
        _logger.info(
            'sprint_a_migration: archived %d demo-dentist record(s): %s',
            len(demo_dentists),
            ', '.join(demo_dentists.mapped('name')),
        )
