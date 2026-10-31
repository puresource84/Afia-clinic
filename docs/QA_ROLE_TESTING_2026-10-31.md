# Afia Clinic 18.0 — role-by-role QA

**Date:** 2026-10-31 · **Branch:** `restructure/18.0-consolidation` · **Build:** one-click install of `afia_clinic` (20 modules)

Driven through the browser against the Docker QA stack, signing in as each
role in turn. Accounts were created with the product's own **Add Staff User**
wizard, not by hand, so the wizard is covered too.

## What each role could actually do

| | Receptionist | Hygienist | Dentist | Administrator |
| --- | :-: | :-: | :-: | :-: |
| Open the clinic | yes | yes | yes | yes |
| Register a walk-in patient | **yes** (PAT/00008) | — | — | yes |
| Create a lab order | **yes** (LAB/2026/00001) | — | — | yes |
| View prescriptions | read-only | read-only | yes | yes |
| **Create** a prescription | **no** | **no** | **yes** (RX/00001) | yes |
| **Create** a treatment plan | — | **no** | yes | yes |
| Clinical Notes menu | no | no | yes | yes |
| Perio Exams menu | no | no | yes | yes |
| Configuration menu | no | **yes** | **yes** | yes |
| Staff menu | no | no | no | yes |

The prescribing boundary is the one that matters most clinically, and it
holds: only the Dentist and the Administrator have a New button on
Prescriptions. Receptionist and Hygienist can read but not create.

Records actually written during the pass: patient PAT/00008, lab order
LAB/2026/00001, prescription RX/00001, plus an invoice raised from a
completed appointment and refused on the second attempt.

## Findings

### 1. Dentist and Hygienist can reach clinic configuration

Both roles see the **Configuration** menu, including the System group:
Shift Times, Online Booking Page, Telegram Messages, Telegram Sent Log.
Those are clinic-administration settings. A dentist changing the online
booking page or the messaging integration is not the intent of the role
matrix, which reserves configuration for the Clinic Administrator.

The Clinical Setup group in the same menu (treatments, medicines,
specialties, medical questions) is defensible for a dentist; the System
group is not.

### 2. Hygienist cannot reach perio charting or clinical notes

The role is defined as "charting and medical questionnaires", and
periodontal charting is normally hygienist work. Today the Hygienist sees
neither Perio Exams nor Clinical Notes — only the Dentist does. Either the
role definition or the menu groups is wrong; a clinic should decide which.

### 3. Receptionist sees clinical menus it cannot use

Dental Charting, Prescriptions and Treatment Plans appear in the
Receptionist's Patients menu. Each opens read-only with no New button, so
this is not an access hole, but offering a menu that leads nowhere is a poor
first impression for the role that uses the system most.

### 4. The Add Staff User wizard uses the old role labels

The wizard still offers "Clinic Dentist", "Clinic Hygienist", "Clinic
Receptionist". The groups were renamed to Dentist, Hygienist and
Receptionist when the role ladder was built; the wizard has its own
hardcoded list and was missed.

## Still not covered

- **Correction (2026-11-01).** This section first claimed no automated test
  runs as a non-administrator. That was wrong, and it was repeated several
  times before anyone checked. Three test files do exactly that, using
  new_test_user and with_user: test_receptionist_access, and the two
  test_access_control files written after the 2026-09-20 audit.

  The real gap was narrower and more specific. Those tests assert **model
  permissions**, and every defect this pass found was a **menu, view or
  asset** fault — a menu the hygienist could not reach though the ACLs
  allowed it, Configuration reachable by a dentist, buttons whose owning
  views sat in no manifest. Nothing in the suite asserted what the
  navigation renders for a given role, so nothing could have caught them.

  Role tests covering both halves were added on 2026-11-01:
  dental_clinical_permissions/tests/test_role_matrix.py for capability
  boundaries and afia_menu/tests/test_role_menus.py for menu visibility.
- The patient portal and online booking were not exercised.
- Telegram and WhatsApp reminders need real credentials.
- The Iraq pack is not installed in this build.
- Arabic interface was not reviewed screen by screen.

## QA accounts on the Docker stack

| Role | Login | Password |
| --- | --- | --- |
| Administrator | `admin` | `admin` |
| Dentist | `dentist@qa.test` | `qatest2026` |
| Hygienist | `hygienist@qa.test` | `qatest2026` |
| Receptionist | `reception@qa.test` | `qatest2026` |

Throwaway credentials for a localhost-only test database. They are not part
of the product and must never reach a clinic install.

---

# Re-test after the fixes

Commit `d8eb675`, verified the same afternoon against the same stack after
`-u afia_dental_core,dental_charting,dental_clinical_permissions`.

| | Receptionist | Hygienist | Dentist | Dentist + manages clinic | Administrator |
| --- | :-: | :-: | :-: | :-: | :-: |
| Configuration menu | no | **no** | **no** | **yes** | yes |
| Staff menu | no | no | no | **yes** | yes |
| Perio Exams menu | no | **yes** | yes | yes | yes |
| Clinical Notes menu | no | no | yes | **yes** | yes |
| Create a prescription | no | no | yes | **yes** | yes |

Findings 1, 2 and 4 are closed. Finding 3 (the Receptionist being shown
read-only clinical menus) is left open by decision, not oversight.

**Configuration** is gone from both the Dentist and the Hygienist, and both
keep everything clinical they had before — the Dentist still shows Clinical
Notes, Perio Exams, Treatment Plans and a New button on Prescriptions.

**Perio Exams** is now on the Hygienist's Patients menu, and the Hygienist
created exam id 1 against a demo patient, which saved and computed its
summary (Avg Pocket Depth 2.0). The ACLs had always allowed this; only the
menu had been in the way.

**The owner-dentist case** was exercised end to end rather than reasoned
about. A new account was created through the wizard's "Dentist (also manages
the clinic)" option; the user record shows **Clinic: Clinic Administrator**,
confirming the option maps to group_clinic_admin. Signed in as that account:
the full clinical menu, a New button on Prescriptions, plus Configuration and
Staff. One role selector, no new group, nothing lost by moving up a rung.

The clinic role selector renders as a single dropdown rather than loose
checkboxes, which confirms the group chain is still linear after this change.

## QA account added

| Role | Login | Password |
| --- | --- | --- |
| Dentist (also manages the clinic) | `ownerdentist@qa.test` | `qatest2026` |

Same throwaway-credential caveat as the table above.
