# Known issues

Things found and deliberately not fixed, so they are a decision rather than
an oversight. Verified on 2026-11-01 against the repository, not recalled.

## Layering

**`afia_dental_core` constrains a field it does not own.**
`models/dental_appointment_fixes.py` declares
`@api.constrains('state', 'apt_start')`, but `apt_start` is defined in
`dental_patient_flow`, which depends on core rather than the other way
round. It never surfaces because the suite installs everything together.
Anyone installing core on its own would hit it. Same class of fault as the
dependency cycles the 18.0 consolidation removed.

## Sequences

Nine `next_by_code()` call sites across the modules, and not all of them
fall back when the sequence record is missing — a clinic whose sequence was
deleted or not loaded gets `False` written into a reference field instead of
a clear error. `dental_lab` was given `sudo()` and a fallback on
2026-10-30; the rest were left alone.

## Files that are in the tree but in no manifest

- `afia_app_launcher/views/res_config_settings_views.xml`
- `afia_dental_core/views/teeth_chart_views.xml`
- `dental_demo_data/data/fix_sprint_a.xml`

Dead unless something references them. This is exactly how the Perio Chart
and Clinical Notes buttons disappeared in October: the only working copies
of those views were in no manifest, so deleting what looked like duplicates
removed the real thing. Worth a static check in CI rather than a cleanup.

## Roles

**The receptionist is shown clinical menus it cannot use.** Dental Charting,
Prescriptions and Treatment Plans appear in the Patients menu and open
read-only with no New button. Not an access hole — the ACLs were tightened
on 2026-11-01 — but a menu that leads nowhere for the role that lives in the
system all day. Left open by decision on 2026-10-31.

## Overlapping patient fields

`clinical_safety.py` carries free-text Allergy, Insurance and Consent fields
on the patient that duplicate the structured models in
`dental_allergy_guard`, `dental_insurance` and `dental_consent`. Two places
to write the same fact, no rule about which wins.

## No CI

Nothing runs the suite automatically. Ninety-odd tests that only run when
someone remembers are a comfort, not a safety net. The launcher background
bug survived months on a warning nobody read.

## Environment traps

**Odoo skips the whole demo dataset if one record is rejected, and exits
0.** It logs `demo data failed to install, installed without demo data` and
carries on. The result is a clean install, a working login, and a clinic
with no patients, dentists or treatments at all. Hit on 2026-11-01 while
adding `demo/demo_today.xml`.

Install warnings — accessibility and duplicate field labels — are listed in
`APP_STORE_SUBMISSION.md` instead, since they matter for store review.
