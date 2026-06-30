<p align="center">
  <img src="modules/dental_hospital/static/description/icon.png" width="80" alt="Afia Clinic"/>
</p>

<h1 align="center">Afia Clinic</h1>
<p align="center">Full-stack dental practice management suite for Odoo 18 CE</p>
<p align="center">
  <img src="https://img.shields.io/badge/Odoo-18%20CE-714B67?style=flat-square&logo=odoo"/>
  <img src="https://img.shields.io/badge/Modules-38-1a73a7?style=flat-square"/>
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

**Linux / Mac:**
```bash
bash install.sh
```

The installer detects your environment automatically:
- **Docker detected** → launches a full Odoo 18 + PostgreSQL stack in containers
- **Odoo CE detected** → copies all 38 modules into your custom_addons and restarts the service
- **Neither found** → guides you to install Docker first

### Step 3 — Open your browser

```
http://localhost:8069
```

Create a new database, go to **Apps**, search for **Dental Hospital** and install it.
All 38 Afia Clinic modules will appear and can be installed from there.

---

## What's Included — 38 Modules

| Category | Modules |
|----------|---------|
| **Foundation** | dental_hospital, clinic_core, clinic_core_plus |
| **Patient Management** | dental_patient_flow, dental_patient_portal, dental_portal_v2, dental_branch |
| **Clinical** | dental_charting_pro, dental_soap_notes, dental_perio_charting, dental_imaging, dental_allergy_guard |
| **Treatment** | dental_treatment_plan, dental_case_acceptance, dental_consent, dental_audit |
| **Lab & Stock** | dental_lab, dental_consumables, dental_sterilization |
| **Insurance** | dental_insurance, dental_insurance_v2 |
| **Booking** | dental_portal_booking, dental_booking_slots, dental_appointment_times |
| **Communication** | dental_communication, dental_reminders_telegram, dental_reminders_whatsapp, dental_telegram_templates |
| **Analytics** | dental_analytics, dental_report_builder |
| **UX & Branding** | dental_ux_fixes, custom_dental_menu, afia_app_launcher |
| **Payments** | payment_paytabs, payment_zaincash |
| **Other** | dental_clinical_permissions, dental_hide_re_tabs, dental_demo_data |

---

## Recommended Install Order

For manual installs, follow this sequence:

1. `dental_hospital` ← install this first
2. `clinic_core`, `clinic_core_plus`
3. All Layer 2 modules (analytics, charting, insurance, treatment plan, etc.)
4. Layer 3+ (soap notes, perio, ux_fixes, allergy guard, audit)

Full install order and test checklist: see [`docs/Install_Guide.docx`](docs/Install_Guide.docx)

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
