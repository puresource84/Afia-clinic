# Removed code — kept for reference only

Nothing here is installed, imported or shipped. Files were moved out of the
live modules on 2026-10-30 during the 18.0 consolidation. Each kept its
original header explaining why it was dead.

| File | Was in | Why it is dead |
| --- | --- | --- |
| `afia_dental_core__teeth_chart.py` | `afia_dental_core/models/` | Legacy flat tooth chart (`teeth.chart`, one boolean per tooth), removed 2026-08-15 and superseded by the FDI odontogram (`dental.tooth.record`) now in `dental_charting`. The file was already emptied of all model code — it contains only its explanatory docstring, so moving it changes no behaviour. |
| `dental_ux_fixes__appointment_invoicing.py` | `dental_ux_fixes/models/` | Byte-for-byte duplicate of `dental_patient_flow/models/appointment_invoicing.py`, which is the one live copy. Found in the 2026-09-20 audit; never imported, never ran. Importing it would register a second competing override of `dental.appointment` invoicing. |

Both were previously left on disk only because the tooling could not delete
files in this folder. That constraint is gone; they are parked here instead
of deleted so the history and reasoning stay findable.

Do not reintroduce either without checking first.
