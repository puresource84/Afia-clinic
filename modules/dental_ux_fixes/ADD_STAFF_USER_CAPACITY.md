# Add Staff User wizard — dentist-seat capacity check

Added 2026-08-21, per Manhel. This documents the enforced dentist-seat cap
added to `clinic.user.wizard` (`wizards/clinic_user_wizard.py` +
`clinic_user_wizard_views.xml`), why it works the way it does, and its
known limitations for future developers.

## What it does

- The wizard form now shows a small colored badge (green/amber/red) in the
  top-right of the dialog — visible **only** when Role = "Clinic Dentist" —
  reading something like "3 of 5 active dentists used — Professional plan".
- If the clinic is at or past its plan's dentist-seat cap (plus the
  existing 10% buffer — same buffer `itcs_license_manager` already uses
  elsewhere), clicking **Create User** with Role = "Clinic Dentist" raises
  a clear `UserError` instead of silently letting the login through.
- No change for the other three roles (Administrator, Hygienist,
  Receptionist) — the ITCS license only tracks two capacity dimensions,
  dentists and patients (see `itcs_license_manager/models/itcs_license.py`),
  so there is nothing to enforce for those roles here.

## Why this needed a design decision, not just plumbing

The ITCS license's `max_dentists` / `active_dentist_count` counts
**`hr.employee` records flagged `is_dentist = True`** — not `res.users`
logins. This wizard creates a `res.users` login and can optionally *link*
it to an *existing* `hr.employee` record, but it never creates or flags an
employee record itself. So strictly speaking, creating a "Clinic Dentist"
role login here does not, by itself, move the needle on
`active_dentist_count` — that only happens if/when someone separately
creates or edits an `hr.employee` record with `is_dentist = True`.

Two designs were possible:
1. **Strict**: only check the cap at the point where an `hr.employee`
   actually gets flagged as a dentist (this already exists — see
   `itcs_license_manager/models/hr_employee_license.py`) and leave this
   wizard alone. Correct in a narrow technical sense, but useless as a
   guardrail — an admin onboarding a new dentist would only find out
   they're over their plan *after* creating the login, when they go edit
   the employee record separately (a different screen, possibly a
   different person/session).
2. **Proxy** (what was built): treat "one more Clinic Dentist login about
   to be created in this wizard" as +1 against the current
   `active_dentist_count`, and check the cap right here, before the login
   is created. Slightly conservative — it will block at the moment of
   onboarding even in the (real but presumably rare) case where the
   Clinic Dentist role is being created for someone who will never
   actually get an `hr.employee` record — but it puts the guardrail where
   the actual workflow happens, which is what was asked for.

Option 2 was built. This is a deliberate approximation, documented here so
a future developer doesn't "fix" it into option 1 without understanding
this was already discussed and rejected as UX-hostile.

## Where the logic lives

- `clinic_user_wizard.py::_capacity_info_html(role)` — builds the badge
  HTML server-side (this is a plain wizard form field, not a list view, so
  it can't reuse the OWL `ListController` patch in
  `itcs_license_manager/static/src/js/list_banner.js` — that only hooks
  list views). Reuses `itcs.license._afia_banner_info('dentist')` for the
  wording/color so the message matches the Patients/Dentists list banners.
- `clinic_user_wizard.py::default_get()` / `_onchange_role_capacity_info()`
  — populate the badge on open and whenever Role changes.
- `clinic_user_wizard.py::action_create_user()` — the actual enforcement,
  right before the `res.users` is created: calls
  `itcs.license._afia_check_cap('dentist', active_dentist_count + 1)`,
  which raises `UserError` past the 110% buffer (same helper
  `hr_employee_license.py` uses) and fires the existing one-time Telegram
  alert to ITCS the moment the plain plan limit is first crossed.
- No changes were made to `itcs_license_manager` itself — this reuses its
  existing public helpers (`get_active_license()`, `_afia_banner_info()`,
  `_afia_check_cap()`) as-is.

## Deploy notes

This adds a **new field** (`capacity_info`) to an existing Python model
(`clinic.user.wizard`) — per the standing rule in
[[odoo-dev-loop-gotchas]] / this project's memory, new/changed Python
fields are NOT picked up by `button_immediate_upgrade` alone; they need a
full Odoo **service restart** first, then `button_immediate_upgrade`
(confirmed repeatedly this project, e.g. the `default_duration` field
incident). No new files were added to the manifest's `data` list, so
`update_list()` is not required this time — restart + upgrade is enough.

Version bumped: `dental_ux_fixes` `18.0.2.1.5` → `18.0.2.1.6`, mirrored to
all 3 package copies (`launch_sprint1_addons`, `Afia Clinic - Unified
Package`, `afia-clinic-repo/modules`).

## 2026-08-21 update — wizard now works standalone without itcs_license_manager

Found while auditing App Store readiness: `_capacity_info_html()` and
`action_create_user()` both called `self.env['itcs.license']`
unconditionally — since `itcs_license_manager` was never declared as a
manifest dependency here, opening this wizard in a build that doesn't have
that module installed would raise `KeyError` immediately (Odoo has no
model named `itcs.license`), for every role, not just Dentist. Guarded
both call sites with `if 'itcs.license' in self.env:` so the wizard now
degrades gracefully — no capacity badge, no cap enforcement, just a plain
staff-creation form — when the license module isn't present. No behavior
change on `db_odoo` (itcs_license_manager stays installed there).

## Not related to the Odoo App Store package

Per Manhel (2026-08-21): this capacity check is part of the private
licensing/AMC layer (`itcs_license_manager` + this wizard's use of it),
built for clinics ITCS sells to directly in Iraq — it is **not** part of
whatever gets packaged for the public Odoo App Store listing. Keep that
separation in mind if `dental_ux_fixes` or `itcs_license_manager` are ever
split or repackaged for App Store submission — this wizard's dependency on
`itcs.license` would need to be removed or made optional first.
