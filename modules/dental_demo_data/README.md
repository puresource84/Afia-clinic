# Dental Demo Dataset

Seeds a realistic Arabic-language demo environment for the Afia Clinic
suite: patients, dentists, treatments, teeth charts, and a mix of
historical (done) and upcoming (draft) appointments. Built for sales
demonstrations, training, and trial instances — **not** intended for
production/customer clinic databases.

## Who this is for

Internal use (sales demos, training) or a throwaway trial instance you
spin up to show a prospect. Do **not** install this on a real clinic's
production database — it will seed fake patient records into it.

## Prerequisites

- A separate database from any real clinic data. Either a brand-new
  database, or one you're comfortable resetting/discarding afterward.
- The core Afia Clinic modules already installed (or installed alongside
  this one in the same command — see below): `afia_dental_core`,
  `dental_charting_pro`, `dental_ux_fixes`. These are declared as
  `depends` in this module's manifest, so Odoo will pull them in
  automatically if they aren't installed yet.

## Important: this module ships its data as "demo" data, not "data"

Odoo has two separate mechanisms for loading a module's XML:

- `'data'` in `__manifest__.py` — always loaded, every install.
- `'demo'` in `__manifest__.py` — only loaded when demo data is enabled
  for the install.

This module's `demo/*.xml` files (dentists, patients, treatments,
appointments) are declared under `'demo'`, **not** `'data'**. This is
intentional — it's the standard Odoo convention for sample/demo content,
and it means the data simply won't appear at all if the target
database/install has demo data disabled.

**If you install this module against a database or config with demo
data suppressed, it will "install successfully" but load zero actual
records — no error, just an empty result.** This is the single most
common way to think this module is broken when it's actually just been
told not to load its content. Concretely: any config file (or `-c` flag)
with `without_demo = True`, or the `--without-demo=all` CLI flag, will
silently skip every file in this module's `demo` list.

## Installing (GUI — recommended for most cases)

1. Create or pick a **non-production** database. When creating a new
   database via the Odoo database manager (`/web/database/manager`),
   make sure the **"Demo data"** checkbox is checked — this is what
   controls whether the `demo` files below will ever be allowed to load
   for this database, for any module, ever.
2. Log in, go to **Apps**, remove the "Apps" filter so all modules show,
   and search for **Dental Demo Dataset**.
3. Click **Install**. Odoo will pull in the core Afia Clinic modules
   automatically if they aren't already installed, then load the demo
   records.
4. Verify: open **Afia Clinic → Patients** — you should see ~30 Arabic
   patient records (e.g. "علي حسين الربيعي"). If the list is empty,
   demo data was disabled for this database — see the note above and
   recreate the database with the "Demo data" checkbox enabled, or use
   the CLI method below with the flag explicitly overridden.

## Installing (command line — for scripted/staging environments)

From the Odoo source checkout, against a **fresh or disposable**
database (adjust paths/DB name for your environment):

```
cd /path/to/odoo
python odoo-bin -c /path/to/your.conf -d your_demo_db \
  -i afia_dental_core,dental_appointment_times,dental_ux_fixes,dental_patient_flow,dental_charting_pro,dental_demo_data \
  --stop-after-init
```

Two things that will silently defeat this:

- If your config file (`your.conf`) has `without_demo = True`, remove
  that line or override it for this run — the demo files will not load
  otherwise, with no error or warning to indicate why.
- Odoo also accepts `--without-demo=` on the command line; make sure
  it's not passed (or is set to an empty value) for a demo install.

To confirm the data actually loaded, check the install log for the
`dental_demo_data` module load line — it should report a meaningful
number of queries (dozens+), not a handful. A near-zero query count for
that module is the tell that demo data was suppressed.

## Uninstalling

Uninstall the module from **Apps** (or `-u`/removal via CLI) to remove
all demo records cleanly. This does not touch any real
configuration/settings made by the core modules.

## Upgrade note (18.0.1.0.0 → 18.0.1.1.0)

A post-install migration script (`migrations/18.0.1.1.0/post-migrate.py`)
runs automatically on upgrade and performs a few cleanup/normalization
steps on the seeded data (default dentist commission %, IQD exchange
rate seed, removing a known blank shift artifact, archiving stray QA/test
patient and "Demo Dentist" records left over from earlier test cycles).
This only runs once, on upgrade past that version — it does not need to
be run manually.
