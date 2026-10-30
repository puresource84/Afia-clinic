# Afia Clinic 18.0 — QA access and test pass

Everything below runs on your own machine. The build that passed the test
suite lives on branch `restructure/18.0-consolidation`; this starts the same
code with the Arabic demo dataset loaded.

## 1. Start it

Docker Desktop must be running.

```powershell
cd "D:\ITCS\ITCS Projects\Dental Clinic Odoo\afia-clinic-repo\docker"
"POSTGRES_PASSWORD=afia_qa_pw" | Out-File -Encoding ascii .env
docker compose up -d
```

First start pulls the images and takes a few minutes. Then create the QA
database. The running server has to be stopped first: it holds open sessions
on the database and binds the port inside the container, so an install run
alongside it fails on both counts.

```powershell
docker compose stop odoo
docker compose exec db dropdb -U odoo --if-exists afia_qa
docker compose run --rm --no-deps odoo odoo -d afia_qa -i afia_menu --stop-after-init
docker compose start odoo
```

`docker compose run` is deliberate: unlike `exec` it starts a throwaway
container that publishes no ports, so it cannot collide with the service.
Dropping the database first is what guarantees the Arabic demo dataset loads
— demo data is only ever loaded at database creation.

`afia_menu` is the glue layer, so installing it alone pulls in all 19 modules
through their dependencies.

## 2. Log in

| | |
| --- | --- |
| URL | http://localhost:8169 |
| Login | `admin` |
| Password | `admin` |

Change the admin password before this is ever reachable from outside your
machine. The stack binds to `127.0.0.1` only, so nothing is exposed by default.

If the login fails, or the Apps list is empty, the module install did not
complete — re-run the four commands above and read the output of the third.

### Scaffolding faults hit on first run (2026-10-30), now fixed

These were in the Docker setup, not in Afia. Listed so nobody debugs them twice:

- `docker/odoo.generated.conf` is produced by `install.ps1`. Running
  `docker compose` without it makes Docker create a *directory* at that path
  and the mount then fails. It is generated now.
- Host port 8069 was already taken on the build machine by another Odoo, so
  the stack publishes **8169** instead.
- `docker compose exec` bypasses the image entrypoint, which is what normally
  injects the database host — so `db_host`/`db_user`/`db_password` are set in
  `odoo.generated.conf` directly.
- Compose took its project name from the folder (`docker`), colliding with an
  unrelated wordpress stack. The project is named `afia-qa` now.

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
