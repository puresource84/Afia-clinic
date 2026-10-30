from . import dental_specialist
from . import dental_time_shift
from . import dental_tooth
from . import dental_treatment  # defines both TreatmentCategory and DentalTreatment
from . import dental_purpose
from . import medicine_frequency
from . import medical_questionnaire
from . import xray_report
from . import res_partner
from . import hr_employee
from . import product_template
from . import account_move
from . import account_payment
from . import dental_appointment
from . import dental_prescription

# merged from clinic_core
from . import res_config_settings

# merged from dental_branch
from . import res_company_branch
from . import dental_appointment_branch
# NOTE: teeth_chart is intentionally NOT imported - see the file header.
# from dental_ux_fixes (dissolved 2026-10-30)
from . import appointment_smart_buttons
from . import dental_appointment_fixes
from . import dental_time_shift_fixes
from . import soft_delete
from . import res_partner_search
from . import res_partner_smart_buttons
from . import clinical_safety
