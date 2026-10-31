<p align="center">
  <img src="modules/afia_dental_core/static/description/icon.png" width="80" alt="Afia Clinic"/>
</p>

<h1 align="center">Afia Clinic</h1>
<p align="center">Full-stack dental practice management suite for Odoo 18 CE</p>
<p align="center">
  <img src="https://img.shields.io/badge/Odoo-18%20CE-714B67?style=flat-square&logo=odoo"/>
  <img src="https://img.shields.io/badge/Modules-36-1a73a7?style=flat-square"/>
  <img src="https://img.shields.io/badge/License-OPL--1-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/Made%20by-ITCS-0d5a8a?style=flat-square"/>
</p>

---

## Quick Install — 3 Steps

### Prerequisites
You need **one** of the following:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) *(recommended — installs everything automatically)*
- [Odoo 18 Community Edition](https://www.odoo.com/page/download) *(if you prefer a native install)*

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/puresource84/Afia-clinic.git
cd Afia-clinic
```

### Step 2 — Run the installer

**Windows (PowerShell as Administrator):**
```powershell
.\install.ps1
```
The Windows installer is a guided wizard: it detects or installs Odoo 18
CE (downloading the official public installer for the same 18.0 CE branch
if it isn't already present), copies the modules, then walks you
through either creating a new database or connecting to one you already
have — no manual steps in Apps needed. If you already have Odoo running,
choose "I already have Odoo running" on the first screen to skip straight
to the database/module step.

**Linux / Mac:**
```bash
bash install.sh
```
Detects Docker or a native Odoo install. With Docker, the first run
generates random database and master passwords into `docker/.env`
(never committed - keep it safe; the master password is needed to create
the database). Without Docker it copies the modules and gives you the
manual install-from-Apps steps below.

### Step 3 — Open your browser

```
http://localhost:8069
```

If you used the Windows installer, modules are already installed and
you're logged in. Otherwise: create a database, go to **Apps**, search
for **Afia Dental Clinic** and install it — the companion modules
appear in the Apps list and can be installed from there based on what
your clinic needs.

---

## What's Included — 36 Modules

| Category | Modules |
|----------|---------|
| **Foundation** | afia_dental_core, clinic_core |
| **Patient Management** | dental_patient_flow, dental_patient_portal, dental_portal_v2, dental_branch |
| **Clinical** | dental_charting_pro, dental_soap_notes, dental_perio_charting, dental_imaging, dental_allergy_guard |
| **Treatment** | dental_treatment_plan, dental_case_acceptance, dental_consent, dental_audit |
| **Lab & Stock** | dental_lab, dental_consumables, dental_sterilization |
| **Insurance** | dental_insurance, dental_insurance_v2 |
| **Booking** | dental_portal_booking, dental_booking_slots, dental_appointment_times |
| **Communication** | dental_communication, dental_reminders_telegram, dental_reminders_whatsapp, dental_telegram_templates |
| **Analytics** | dental_analytics |
| **UX & Branding** | dental_ux_fixes, custom_dental_menu, afia_app_launcher |
| **Payments** | payment_paytabs, payment_zaincash |
| **Other** | dental_clinical_permissions, dental_demo_data, itcs_license_manager (ITCS internal) |

**v1.1 scope (single clinic, cash payments, Telegram + email reminders).**
The Windows installer does not auto-install `dental_branch`,
`dental_reminders_whatsapp`, `payment_paytabs` or `payment_zaincash`;
they remain in `modules/` but are not production-ready for v1.1.

`dental_demo_data` seeds fake Arabic patient records for sales demos and
training — install it only on a separate, disposable database, never on
a real clinic's production database. See `modules/dental_demo_data/README.md`.

---

## Recommended Install Order

For manual installs, follow this sequence:

1. `afia_dental_core` ← install this first (the only standalone "App";
   nothing else auto-installs with it on purpose)
2. `clinic_core`
3. Companion modules grouped by what your clinic needs (charting,
   scheduling/reminders, insurance/billing, operations, admin, branding)

Full walkthrough: [`docs/Afia_Clinic_v1_Install_Guide.docx`](docs/Afia_Clinic_v1_Install_Guide.docx).

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Odoo | 18.0 Community Edition |
| PostgreSQL | 14+ |
| Python | 3.10+ |
| Docker *(optional)* | 24+ |

---

## About

**Afia Clinic** (عافية) is a complete dental practice management suite built on Odoo 18 CE by **ITCS — IT Corner Solutions**.

Designed for dental clinics in the Arab world with full Arabic/RTL support, bilingual patient communication, and integration with local payment providers (PayTabs, ZainCash).

- Website: [itcornersolutions.net](https://www.itcornersolutions.net/)
- License: OPL-1 (Odoo Proprietary License)
- Odoo Apps: [Coming soon]

---

<p align="center">Made with care by <a href="https://www.itcornersolutions.net/">ITCS</a></p>
