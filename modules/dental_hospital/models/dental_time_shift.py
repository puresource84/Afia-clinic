# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DentalTimeShift(models.Model):
    """Doctors time shift, different time slots"""
    _name = 'dental.time.shift'
    _description = "Dental Time Shift"
    _rec_name = 'name'

    name = fields.Char(string='Name', readonly=True,
                       help="name of the time shifts")
    shift_type = fields.Selection(
        selection=[('morning', 'Morning'), ('day', 'Day'),
                   ('evening', 'Evening'), ('night', 'Night')],
        string="Shift Type", help="Selection field for the shift type")
    start_time = fields.Float(string="Start Time", help="start time of time slot")
    end_time = fields.Float(string="End Time", help="End time of time slot")

    @api.model_create_multi
    def create(self, vals_list):
        """Overrides the default create method to set the `name` field of the
        newly created `dental.time.shift` record(s) to a string that represents
        the shift time range."""
        res = super(DentalTimeShift, self).create(vals_list)
        res.name = f'{res.start_time} to {res.end_time}'
        return res

    @api.onchange('start_time', 'end_time')
    def _onchange_time(self):
        name = f'{self.start_time} to {self.end_time}'
        self.update({'name': name})

