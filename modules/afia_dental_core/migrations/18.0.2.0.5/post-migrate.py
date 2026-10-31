# -*- coding: utf-8 -*-
"""2026-08-21, per Manhel — backfill for the is_patient auto-sync fix.

Before this version, account.move.create()/write() never propagated
is_treatment_invoice=True to partner_id.is_patient. Any customer used on a
treatment invoice through a path other than the Patients app's own "New"
button (e.g. the invoice form's inline Customer quick-create) was left with
is_patient=False, making them silently invisible on views that filter on
partner_id.is_patient = True (Invoices, Payments, some Reporting pivots) —
even though the invoice itself was perfectly valid, posted, and paid.

This is a one-time backfill: flag every partner who is the customer on at
least one existing treatment invoice, so already-created invoices (e.g.
INV/2026/00057, partner "بتول الحلبي") become visible immediately without
Manhel needing to recreate them. Going forward, the ORM-level fix in
account_move.py (_sync_patient_flag) keeps new/edited invoices in sync.

Deliberately does NOT touch patient_no/medical questionnaire seeding here —
res.partner.write({'is_patient': True}) via the ORM (not raw SQL) is used
so ResPartner.write()'s own _onboard_new_patients() hook runs normally and
assigns a patient number / seeds the questionnaire exactly as if the
partner had been onboarded through the UI.
"""


def migrate(cr, version):
    if not version:
        return
    env = _get_env(cr)
    partners = env['res.partner'].search([
        ('is_patient', '=', False),
        ('id', 'in', _treatment_invoice_partner_ids(env)),
    ])
    if partners:
        partners.write({'is_patient': True})


def _treatment_invoice_partner_ids(env):
    env.cr.execute("""
        SELECT DISTINCT partner_id
        FROM account_move
        WHERE is_treatment_invoice = TRUE
          AND partner_id IS NOT NULL
    """)
    return [row[0] for row in env.cr.fetchall()]


def _get_env(cr):
    from odoo import api, SUPERUSER_ID
    return api.Environment(cr, SUPERUSER_ID, {})
