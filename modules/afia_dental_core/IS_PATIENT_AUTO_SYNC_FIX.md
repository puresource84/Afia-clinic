# Invisible treatment invoices — is_patient auto-sync fix

Added 2026-08-21, per Manhel's bug report: a real, posted, paid invoice
(INV/2026/00057, customer "بتول الحلبي") did not appear on the Invoices
list even though it was created and paid successfully.

## Root cause

`res.partner.is_patient` (`afia_dental_core/models/res_partner.py`) is a
plain stored boolean, `default=False`. The only place that ever set it to
`True` was the context default (`default_is_patient: True`) on the
Patients app's own "New" button
(`afia_dental_core/views/res_partner_views.xml`).

Invoices, Payments, and some Reporting pivots filter on
`partner_id.is_patient = True`. Any customer created or selected through a
different path — e.g. an invoice's inline Customer quick-create, or simply
picking an existing non-flagged contact — never got that flag set, so
their invoices/payments were silently excluded from those filtered views,
with no error and no visual indicator that anything was wrong.

`account.move.is_treatment_invoice` is set correctly via a context default
on the Invoices action, but nothing propagated that flag onto the
partner's `is_patient` field.

## Fix

`afia_dental_core/models/account_move.py`:
- `create()` and `write()` overrides now call `_sync_patient_flag()`
  whenever a move is (or becomes) a treatment invoice — flips
  `partner_id.is_patient = True` if it isn't already.

`afia_dental_core/models/res_partner.py`:
- The patient-onboarding logic that used to live only in `create()`
  (assign `patient_no`, seed the medical questionnaire) was extracted
  into `_onboard_new_patients()` and is now also called from a new
  `write()` override whenever a partner's `is_patient` flips from False to
  True after the record already exists — so partners auto-flagged by the
  invoice fix above get a proper patient number and questionnaire too, not
  just the boolean.

`afia_dental_core/migrations/18.0.2.0.5/post-migrate.py`:
- One-time backfill: finds every partner who is the customer on at least
  one existing `is_treatment_invoice=True` move and flags them via the
  ORM (`res.partner.write`, not raw SQL) so the normal `write()` hook
  above runs and assigns them a patient number too. This is what made
  Manhel's already-created invoice (and 7 other previously-hidden ones for
  the same customer) visible immediately without recreating anything.

## Verified

- Backfill: partner id 1103 ("بتول الحلبي") flipped `is_patient: false →
  true`, assigned `patient_no: PAT/00002`; all 8 of her invoices
  (including INV/2026/00057) now match the Invoices list's domain filter.
- Forward fix (live, not just migration): created a fresh non-patient test
  partner, created a treatment invoice for them via RPC — partner was
  auto-flagged `is_patient: true` with a fresh `patient_no` immediately on
  invoice creation. Test invoice and partner were deleted after
  confirming.

## Scope check — Policies / Insurers / Claims

Manhel asked to check "the rest of similar documents, such as policies,
insurer, etc." Checked their action definitions
(`dental.insurer` / `dental.policy` / `dental.claim`, actions 989/990/991):
none of them have a domain filter at all (`domain: false`). They aren't
filtered by `partner_id.is_patient` or anything else, so this specific bug
class does not apply to them — nothing to fix there.

## Deploy notes

New Python field-adjacent logic (create/write overrides) + a new
migrations folder — per the standing project rule, this needed a full
service restart before `update_list()` + `button_immediate_upgrade` would
pick it up. Version bumped `afia_dental_core` `18.0.2.0.4` → `18.0.2.0.5`,
mirrored to all 3 package copies (`launch_sprint1_addons`, `Afia Clinic -
Unified Package`, `afia-clinic-repo/modules`).
