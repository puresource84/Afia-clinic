# Afia Clinic 18.0 — QA access and test pass

Everything below runs on your own machine. The build that passed the test
suite lives on branch `restructure/18.0-consolidation`; this starts the same
code with the Arabic demo dataset loaded.

## 1. Start it

Docker Desktop must be running. From the repo root:

```powershell
cd docker
"POSTGRES_PASSWORD=afia_qa_pw" | Out-File -Encoding ascii .env
docker compose up -d
```

First start pulls the images and takes a few minutes. Then create the QA
database with everything installed in one command:

```powershell
docker compose exec odoo odoo -d afia_qa -i afia_menu --stop-after-init
docker compose restart odoo
```

`afia_menu` is the glue layer, so installing it alone pulls in all 19 modules
through their dependencies.

## 2. Log in

| | |
| --- | --- |
| URL | http://localhost:8069 |
| Login | `admin` |
| Password | `admin` |

Change the admin password before this is ever reachable from outside your
machine. The stack binds to `127.0.0.1` only, so nothing is exposed by default.

If the login fails, the database was created without demo data — drop it and
re-run the command in step 1, which creates it with demo data on.

## 3. Create one user per role

The demo dataset ships patients, dentists, treatments and appointments, but no
user accounts. Role behaviour is the main thing to check, so make one of each:

**Settings → Users & Companies → Users → New.** Set a login and password, then
under the **Clinic** category pick one role per user:

| Role | Should be able to | Should NOT be able to |
| --- | --- | --- |
| Clinic Receptionist | register patients, book and reschedule appointments, take payment, create lab orders and insurance claims | open clinical notes, edit treatment plans, prescribe |
| Clinic Dentist | everything reception can, plus charting, perio, SOAP notes, treatment plans, prescriptions | clinic configuration |
| Clinic Hygienist | charting and questionnaires | prescribe, edit treatment plans |
| Clinic Administrator | everything, including configuration | — |

The roles now cascade: Administrator includes Dentist, which includes
Receptionist. This was unified on 2026-10-30 — Afia previously shipped two
different sets of roles with the same names.

## 4. What to test, in priority order

These are the behaviours that changed, or that the automated tests cannot
reach. Everything here is worth a few minutes.

### Fixed this week — confirm each actually works

- [ ] **Register a walk-in patient as the Receptionist.** This used to crash.
- [ ] **Create a lab order as the Receptionist.** This used to fail with a
      permissions error.
- [ ] **Create an insurance claim as the Receptionist.**
- [ ] **Delete an appointment, then open the calendar.** The slot must be
      free. It used to leave a ghost booking behind.
- [ ] **Open an appointment form.** Count the stat buttons across the top —
      Dental Chart, Claims, Prescriptions, Invoices, Perio Chart, Clinical
      Notes. None should appear twice.
- [ ] **Complete an appointment and invoice it, twice.** The second attempt
      must refuse. Check the invoice includes the prescription's medicines.
- [ ] **Open a treatment plan, consent form, lab order and sterilisation log.**
      The chatter at the bottom should render normally, not as raw tables.

### Core clinical flow

- [ ] Book → confirm → start → complete an appointment
- [ ] Odontogram: record a condition on a tooth, check it shows on the chart
- [ ] Perio chart, SOAP note, treatment plan, consent form
- [ ] Prescription with medicines, and its printed PDF
- [ ] Patient portal: book from the website as a patient
- [ ] Arabic: switch the interface to Arabic and check the main screens

### Known gaps — do not treat as new bugs

- Telegram and WhatsApp reminders need real credentials; untested here.
- The Iraq pack (licence manager, PayTabs, ZainCash) is **not** installed in
  this QA build and has not been tested.
- `clinical_safety` adds free-text Allergy, Insurance and Consent fields on the
  patient that duplicate the structured models. Known, documented, unresolved.

## 5. Reporting what you find

For anything that looks wrong, note the role you were using, the screen, and
what you expected. Role matters more than anything else — most of what was
broken this week was only visible to a non-administrator.

## Version this QA build matches

| | |
| --- | --- |
| Branch | `restructure/18.0-consolidation` |
| Modules | 19 global (Iraq pack excluded) |
| Test result | 76 tests, 0 failures — `docs/TEST_REPORT_2026-10-30.md` |
| Odoo in Docker | `odoo:18.0-20251222` (pinned image) |
| Odoo used for the test run | 18.0 branch, commit `96dc447e` |

Those last two are close but not byte-identical. If QA hits something the
tests did not, the image difference is worth ruling out first.
