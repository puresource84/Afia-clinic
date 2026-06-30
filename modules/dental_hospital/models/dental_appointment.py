from odoo import models, fields, api, _


class DentalAppointment(models.Model):
    _name = 'dental.appointment'
    _description = 'Dental Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'appointment_no' # Set appointment_no as the display name



    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain="[('is_patient', '=', True)]")
    tooth_ids = fields.Many2many('dental.tooth', string="Teeth Affected")
    user_name = fields.Char(string="Responsible", default=lambda self: self.env.user.name)

    patient_no = fields.Char(string='Patient No.',help="Type or select Patient No.")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    age = fields.Integer(string='Age')
    mobile = fields.Char(string='Mobile')
    appointment_no = fields.Char(string='Appointment No.', readonly=True, copy=False)  # Unique appointment number

    appointment_date = fields.Date(
        string='Date', required=True,store=True,
        help="Date when the appointment is scheduled"
    )

    urgency = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent')
    ], string='Treatment Type')
    patient_categ = fields.Selection([('old', 'Old'),('new','New')],string='Patient Category')

    # purpose = fields.Many2many('dental.purpose', string='Purpose')
    treatments = fields.Many2many('dental.treatment', string='Treatments')
    dentist_id = fields.Many2one(
        'hr.employee',
        string='Dentist',
        required=True,
        domain="[('is_dentist', '=', True)]"
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    time_shift_ids = fields.Many2many('dental.time.shift',
                                      string="Available Times",
                                      help="Choose the time shift",
                                      compute='_compute_time_shifts')
    shift_id = fields.Many2one('dental.time.shift',
                               string="Booking Time",
                               domain="[('id','in',time_shift_ids)]",
                               help="Choose the time shift")


    @api.model_create_multi
    def create(self, vals_list):
        """ Assign Patient No. only if the patient does not have one and update details in res.partner """
        for vals in vals_list:
            if vals.get('patient_id'):
                patient = self.env['res.partner'].browse(vals['patient_id'])

                # Ensure patient_no is assigned correctly
                if not patient.patient_no or patient.patient_no == 'New':
                    patient_no = self.env['ir.sequence'].next_by_code('dental.patient') or 'PAT/NEW'
                    patient.write({'patient_no': patient_no})  # Save it in the database
                    vals['patient_no'] = patient_no  # Assign the same to appointment
                else:
                    vals['patient_no'] = patient.patient_no  # Use existing patient_no

                # Ensure patient details are updated in res.partner
                patient.write({
                    'is_patient': True,
                    'gender': vals.get('gender', patient.gender),
                    'patient_age': vals.get('age', patient.patient_age),
                    'mobile': vals.get('mobile', patient.mobile),
                })

            # Generate unique Appointment Number
            if not vals.get('appointment_no'):
                vals['appointment_no'] = self.env['ir.sequence'].next_by_code('dental.appointment') or 'APT/NEW'

            # Set responsible user if missing
            if not vals.get('user_name'):
                vals['user_name'] = self.env.user.name

        return super(DentalAppointment, self).create(vals_list)


    @api.onchange('patient_no')
    def _onchange_patient_no(self):
        """ Auto-fill patient details based on entered Patient No. """
        if self.patient_no:
            patient = self.env['res.partner'].search([('patient_no', '=', self.patient_no)], limit=1)
            if patient:
                self.patient_id = patient.id
                self.gender = patient.gender
                self.age = patient.patient_age
                self.mobile = patient.mobile
            else:
                self.patient_id = False
                self.gender = False
                self.age = False
                self.mobile = False
    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        """ Auto-fill patient_no and patient details if the patient exists. """
        if self.patient_id:
            # Ensure patient_no is generated for newly created patients
            if not self.patient_id.patient_no or self.patient_id.patient_no == 'New':
                self.patient_id.write({'patient_no': self.env['ir.sequence'].next_by_code('dental.patient')})

            self.patient_no = self.patient_id.patient_no  # Use assigned patient_no
            self.gender = self.patient_id.gender
            self.age = self.patient_id.patient_age
            self.mobile = self.patient_id.mobile
            self.patient_id.is_patient = True  # Mark as patient

        # Also set current user as responsible
        self.user_name = self.env.user.name

    @api.depends('dentist_id')
    def _compute_time_shifts(self):
        """To get the doctors time shift"""
        for record in self:
            record.time_shift_ids = self.env['dental.time.shift'].search(
                [('id', 'in', record.dentist_id.time_shift_ids.ids)]).ids
    def action_confirm(self):
        """ Confirm the appointment and move to 'confirmed' state """
        for rec in self:
            if not rec.patient_no:
                rec.patient_no = rec.patient_id.patient_no  # Use existing patient_no
            rec.state = 'confirmed'

    def action_open_patient_form(self):
        """ Opens the form view of the patient when appointment is confirmed """
        self.ensure_one()
        if self.state == 'confirmed':  # Ensure the button is visible only in confirmed state
            self.state = 'in_progress'
            return {
                'type': 'ir.actions.act_window',
                'name': 'Patient Form',
                'res_model': 'res.partner',
                'view_mode': 'form',
                'res_id': self.patient_id.id,
                'target': 'current',
            }



    def action_done(self):
        """ Mark appointment as Done when treatment is complete """
        self.state = 'done'

    def action_cancel(self):
        """ Cancel appointment """
        self.state = 'cancelled'
