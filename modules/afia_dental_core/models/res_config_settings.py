from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    clinic_default_appointment_duration = fields.Integer(
        string="Default Appointment Duration (minutes)",
        default=30,
        config_parameter='afia_dental_core.clinic_default_appointment_duration'
    )
    clinic_appointment_grace_period = fields.Integer(
        string="Appointment Grace Period (minutes)",
        default=10,
        config_parameter='afia_dental_core.clinic_appointment_grace_period'
    )
    clinic_require_patient_mobile = fields.Boolean(
        string="Require Patient Mobile",
        default=True,
        config_parameter='afia_dental_core.clinic_require_patient_mobile'
    )
    clinic_enable_whatsapp_reminders = fields.Boolean(
        string="Enable WhatsApp Reminders",
        default=False,
        config_parameter='afia_dental_core.clinic_enable_whatsapp_reminders'
    )