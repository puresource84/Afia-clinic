from . import dental_appointment_fixes
from . import appointment_smart_buttons
from . import dental_time_shift_fixes
from . import res_partner_search
from . import res_partner_smart_buttons
from . import clinical_safety
from . import commission_report
from . import soft_delete

# appointment_invoicing.py (action_view_invoices / action_create_invoice /
# invoice_ids / invoice_count on dental.appointment, referenced by this
# module's own dental_appointment_view_fix.xml) lives in dental_patient_flow
# now — see that module's models/__init__.py. Not imported here; this
# module's own copy of the file is a stale leftover from before the move
# and is intentionally left out of models/__init__.py. 