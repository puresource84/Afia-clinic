from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_dentist = fields.Boolean(string="Is a Dentist")
    employee_type = fields.Selection(selection_add=[
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist')
    ],ondelete={'doctor': 'set default', 'receptionist': 'set default'})

