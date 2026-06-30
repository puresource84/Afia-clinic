# Clinic Core Plus

## Install & Smoke Test Checklist

### Install Steps
1. Update the module list: `odoo -u clinic_core_plus` or use the Apps menu to update.
2. Install the module from the Apps menu.

### Where to Find the Menu
- Navigate to: **Dental Hospital -> Configuration -> Core Settings**

### Verify Persistence Steps
1. Set values in the Core Settings form.
2. Save the settings.
3. Confirm the values are stored in `ir.config_parameter`:
   - `clinic_core_plus.clinic_default_appointment_duration`
   - `clinic_core_plus.clinic_appointment_grace_period`
   - `clinic_core_plus.clinic_require_patient_mobile`
   - `clinic_core_plus.clinic_enable_whatsapp_reminders`

### Access Check
- Ensure only users in the **Clinic Administrator** group can see the Core Settings menu.