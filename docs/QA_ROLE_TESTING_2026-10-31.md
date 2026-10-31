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

- **No automated test runs as a non-administrator.** Every defect found over
  the last two days was invisible to the 76-test suite for this reason. A
  handful of tests that act as each role is the highest-value thing to add
  before store submission; this document lists the scenarios to write.
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
