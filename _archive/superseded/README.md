# Superseded code — kept for reference only

## `chatter_fixes.xml` and `dental_claim_form_fix.xml`

Both were inherited `ir.ui.view` records that patched the deprecated
`<div class="oe_chatter">` pattern into Odoo 18's `<chatter/>` tag at runtime,
across five modules (treatment plan, consent, lab, sterilization, insurance).

Removed 2026-10-30: the deprecated markup was corrected **in the source form
views themselves**, so the patches have nothing left to patch. This also
removed a dependency cycle — the patch file lived in `afia_dental_core` and
had to reference `dental_consent`, `dental_lab`, `dental_sterilization` and
`dental_treatment_plan`, all of which depend on core.

Five inherited views deleted, five source views corrected. Net behaviour is
identical; the form renders the same chatter.
