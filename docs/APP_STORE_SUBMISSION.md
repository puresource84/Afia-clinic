# Submitting Afia Clinic to the Odoo App Store

Checked against Odoo's own upload page on 2026-11-01. Everything below that
is marked unverified is exactly that — it is recorded so the next person
does not mistake it for a settled fact, which is how the wrong version of
this page nearly got written.

## It is a Git repository, not a zip

Odoo's upload page asks you to **register a Git repository**, in the form:

```
ssh://git@gitServer(:port)/mypath#version
```

with `ssh://git@github.com/odoo/odoo#9.0` as its own example. The `#version`
suffix names the branch or tag to publish from.

A widely-cited vendor blog says the store takes a zip upload with the module
folder at the archive root. That contradicts Odoo's own page and should not
be followed. It is plausibly describing an older flow.

**What this means for us:** the `18.0` branch, cut on 2026-11-01, is already
the right shape. Nothing needs restructuring for the submission mechanism
itself.

## What the page requires of each module

| | Required | Afia status |
| --- | --- | --- |
| `__manifest__.py` | yes | present in all 20 |
| `static/description/icon.png`, genuinely PNG | yes | present in all 20 |
| `static/description/index.html` | yes | **missing from `afia_clinic`**, present in the other 19 |
| `images` manifest key | yes | present on `afia_clinic`; no screenshots yet |
| `LICENSE` at module or repository root | yes | present at repository root |
| `license` manifest key | defaults to Other Proprietary if omitted | `OPL-1` throughout |
| `price` / `currency` | paid modules only; EUR or USD | 299 USD on `afia_clinic` |
| `doc/index.rst` | optional, must be valid pure rst | absent, which is fine |

The page also notes that the **first image whose name ends in `_screenshot`**
is the one displayed large on the listing. We have no screenshots at all, so
the listing would currently show only the banner.

## Open questions, not yet answered

- **Does Odoo scan the repository recursively for modules?** Ours live under
  `modules/`, not at the repository root. The upload page does not say either
  way. It does say one repository may hold many modules, and that the LICENSE
  may sit at the repository root, which hints at tolerance for structure —
  but that is inference, not documentation. Settle this before submitting;
  flattening `modules/` afterwards would be disruptive.
- **Image dimensions.** Odoo's page states formats (png, gif, jpeg) but no
  pixel sizes. The 1280x600 banner and 128x128 icon figures that circulate
  come from a vendor blog, not from Odoo. Our banner is 1480x846.

## Before submitting

1. Write `afia_clinic/static/description/index.html` — the listing page.
2. Capture screenshots and add them to `images`, the headline one named to
   end in `_screenshot`.
3. Resolve the repository-layout question above.
4. Manhel's own QA pass, which has not happened yet.

## Source

Odoo, *Submit your Apps and Themes*: https://apps.odoo.com/apps/upload

## Quality warnings from a clean install

A fresh install of all 20 modules on Odoo 18 raises 55 warnings and one
error. None break anything, but the store names "code quality issues" as a
rejection reason, so they are listed here rather than discovered by a
reviewer.

- **Accessibility**, the bulk of them: `<i>` elements carrying a Font Awesome
  class with no title and no text, in the patient-flow kanban views and the
  patient kanban in `afia_menu`. A screen reader announces nothing for them.
- **Duplicate field labels**: `invoice_count` and `invoice_ids` on
  `dental.appointment` are both labelled "Invoices"; `dob` collides with
  Odoo's own `birthday` on `hr.employee` and `res.users`.
- **A non-searchable field in a dependency**: `dental.perio.exam.prev_exam_id`
  is depended on by `prev_exam_date`, which Odoo warns will not recompute
  reliably.
- `dental.treatment.plan.line.state` passes a `tracking` parameter the field
  type does not accept, which Odoo ignores.
- The one error, an RST title underline shorter than its title in
  `afia_clinic`'s manifest description, is fixed.
