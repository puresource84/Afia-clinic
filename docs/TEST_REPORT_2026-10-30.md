# Afia Clinic 18.0 — test report

**Date:** 2026-10-30 · **Branch:** `restructure/18.0-consolidation` · **Result: PASS**

This is the release record for the 18.0 consolidation. It is the answer to
"when did we last test this, and what did it say".

## Result

| | |
| --- | --- |
| Modules installed | **19 / 19** |
| Critical errors | **0** |
| Afia tests | **76 run — 0 failed, 0 errors** |
| Full-suite run (Odoo's own tests included) | 5,063 tests |

```
odoo.tests.result: 0 failed, 0 error(s) of 76 tests
```

### Per module

| Module | Tests | Time | Queries |
| --- | ---: | ---: | ---: |
| afia_dental_core | 44 | 3.04s | 2,658 |
| dental_charting | 20 | 0.43s | 331 |
| dental_reminders | 16 | 0.22s | 172 |
| dental_patient_flow | 8 | 5.66s | 4,690 |
| dental_insurance | 5 | 0.37s | 406 |
| dental_lab | 5 | 0.41s | 382 |
| dental_clinical_permissions | 4 | 0.45s | 330 |

Modules with no tests of their own: afia_app_launcher, afia_menu,
dental_allergy_guard, dental_analytics, dental_audit, dental_consent,
dental_consumables, dental_demo_data, dental_portal, dental_sterilization,
dental_treatment_plan. They are covered only by installing cleanly.

## Environment

| | |
| --- | --- |
| Odoo | 18.0, commit `96dc447e` |
| PostgreSQL | 16.15 |
| Python | 3.12.3 |
| Database | created fresh, demo data on |
| Command | `odoo-bin -d afia_test -i <all 19> --test-enable --stop-after-init` |

## What it took: eight runs

Each run failed on a real defect, was fixed, and re-run.

| Run | Modules | Stopped by |
| --- | ---: | --- |
| 1 | 1/19 | Aggregation files (appointment smart buttons) placed in core instead of the menu layer, referencing modules that depend on core |
| 2 | 4/19 | Bare, unqualified references to security groups that had been moved to core |
| 3 | 4/19 | `button_box` on the appointment form had no owner; three modules coordinated through view-priority numbers |
| 4 | 17/19 | Controller file renamed on collision during the portal merge; its import was not updated |
| 5 | 19/19 | Installed. 3 Afia test failures |
| 6 | 19/19 | 2 errors — `setUpClass` using the Odoo 19/20 field name `group_ids` |
| 7 | 19/19 | 2 errors — two genuine access-control bugs |
| 8 | 19/19 | **PASS** |

## Defects found and fixed

### Found by the tests

1. **Deleting an appointment left a ghost calendar booking.** `soft_delete.py`
   overrides `unlink()` on `dental.appointment` to archive instead of delete,
   and never calls `super()`. Core's own `unlink()`, which removes the linked
   calendar event, was dead code. The slot stayed booked on the dentist's
   calendar for an appointment that no longer existed. Soft delete is correct
   for a clinic (the clinical record is kept for audit) but it must free the
   slot — it now deactivates the calendar event, matching `action_cancel()`.
2. **Receptionists could not create lab orders.** `dental.lab.order.create()`
   called `next_by_code()` without `sudo()`, so numbering a new lab order
   required admin rights.
3. **The Receptionist role did not make its holder an internal user.**
   `group_dental_reception` had no `implied_ids`. A user holding only that
   group could not read `mail.message.subtype`, so creating any chattered
   record — a claim, a lab order — failed with an AccessError.
4. **A test had been failing silently since 1 September.**
   `test_next_appointment_date_creates_follow_up` hardcoded `2026-09-01`,
   which was in the future when written. Now relative to today.
5. **`odontogram_data` test drift.** The field returns
   `{'condition': ..., 'surfaces': [...]}` per tooth; the test still expected
   a bare string from before surfaces were added.

### Found while restructuring

6. **Duplicate stat buttons on the appointment form.** The Perio Chart and
   Clinical Notes buttons were added both by their owning modules and again
   by the menu layer.
7. **Two dependency cycles**, both fixed at the root: a chatter patch that
   forced core to depend on its own dependents (the deprecated markup is now
   corrected in the five source views, and all five patch views deleted), and
   security groups scattered across three modules (all five clinic roles now
   live in core, with a pre-migration that re-points the moved
   `ir.model.data` rows so existing databases keep their group memberships).

## Open findings — not fixed, needs a decision

### 1. Two parallel role hierarchies (highest priority)

`afia_dental_core` defines **two complete and separate sets of clinic roles**,
in two files:

| `security/clinic_security.xml` | `security/security_groups.xml` |
| --- | --- |
| `group_clinic_admin` | `group_dental_manager` ("Clinic Administrator") |
| `group_clinic_dentist` | `group_dental_dentist` ("Dentist") |
| `group_clinic_receptionist` | `group_dental_reception` ("Receptionist") |
| `group_clinic_hygienist` | |
| `group_dental_clinician` | |

Different modules point their ACLs at different sets — `dental_insurance` and
`dental_lab` use `group_dental_reception`, most others use `group_clinic_*`.
Two groups named "Receptionist" with different permissions can be assigned
from the same settings screen, and which one an administrator picks silently
decides what that employee can do.

Merging them changes who can do what in a live clinic, so it is a product
decision, not a refactor. It should be settled before the first paying install.

### 2. Nine unguarded `next_by_code()` calls

Besides the lab order above, sequence numbering is called without `sudo()` in
`dental_appointment` (×2), `dental_prescription`, `res_partner`,
`dental_consent`, `dental_claim`, `sterilization_log` and `treatment_plan`.
These pass today because an internal user can read `ir.sequence`, but they
depend on that ACL staying as it is. Worth normalising.

### 3. Overlapping patient fields

`clinical_safety.py` adds `allergy_alert`, `insurance_notes`, `consent_signed`
and `consent_date` as free text on `res.partner`, duplicating the structured
`dental.patient.allergy`, `dental_insurance` and `dental_consent` models. The
same clinical fact can be recorded in two places and disagree. Moved into core
unchanged — deliberately not rewired before the suite was green.

## What this report does NOT cover

- **No browser or tour tests.** Nothing here exercises the UI in a browser.
- **No manual verification.** No human has clicked through a clinic workflow
  on this build.
- **Demo data only.** No test against a real clinic database or an upgrade
  from a previous Afia version.
- **The Iraq pack is untested.** `itcs_license_manager`, `payment_paytabs` and
  `payment_zaincash` were not installed in this run.
- Odoo's own suite reports 12 unrelated errors in this environment
  (`phone_validation`, a barcode rendering test) caused by optional libraries
  missing from the test container, not by Afia.
