# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DentalDoctor(models.Model):
    """To add the doctors of the clinic"""
    _inherit = 'hr.employee'

    job_position = fields.Char(string="Designation",
                               help="To add the job position of the doctor")
    specialised_in_id = fields.Many2one('dental.specialist',
                                        string='Specialised In',
                                        help="Add the doctor specialised")
    dob = fields.Date(string="Date of Birth",
                      required=True,
                      help="DOB of the patient")
    doctor_age = fields.Integer(compute='_compute_doctor_age',
                                store=True,
                                string="Age",
                                help="Age of the patient")
    sex = fields.Selection([('male', 'Male'),
                            ('female', 'Female')],
                           string="Sex",
                           help="Sex of the patient")
    time_shift_ids = fields.Many2many('dental.time.shift',
                                      string="Time Shift",
                                      help="Time shift of the doctor")
    is_dentist = fields.Boolean(string="Is a Dentist")
    employee_type = fields.Selection(selection_add=[
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist')
    ], ondelete={'doctor': 'set default', 'receptionist': 'set default'})
    reg_no = fields.Char(string="Register No:")

    @api.model_create_multi
    def create(self, vals):
        """Automatically create an internal user with mobile login"""
        if 'mobile_number' in vals and vals['mobile_number']:
            existing_user = self.env['res.users'].search([('login', '=', vals['mobile_number'])])
            if existing_user:
                raise ValueError("Mobile number already exists for another user!")

        doctor = super(DentalDoctor, self).create(vals)

        if doctor.mobile_phone:  # Ensure a mobile number is available for login
            user_vals = {
                'name': doctor.name,
                'login': doctor.mobile_phone,  # Set mobile number as login username
                'employee_id': doctor.id,
                # 'groups_id': [(4, self.env.ref('dental.group_doctor').id)],  # Assign Doctor Group
                'company_id': doctor.company_id.id,
            }
            new_user = self.env['res.users'].create(user_vals)
            doctor.user_id = new_user.id  # Assign the created user to the doctor

        return doctor

    def unlink(self):
        """Delete the corresponding user from res.users while
        deleting the doctor"""
        for record in self:
            self.env['res.users'].search([('id', '=', record.user_id.id)]).unlink()
        res = super(DentalDoctor, self).unlink()
        return res

    @api.depends('dob')
    def _compute_doctor_age(self):
        """To calculate the age of the doctor from the DOB"""
        for record in self:
            record.doctor_age = (fields.date.today().year - record.dob.year -
                                  ((fields.date.today().month,
                                    fields.date.today().day) <
                                   (record.dob.month,
                                    record.dob.day))) if record.dob else False
