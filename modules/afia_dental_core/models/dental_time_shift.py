# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DentalTimeShift(models.Model):
    _name = 'dental.time.shift'
    _description = 'Dental Time Shift'
    _rec_name = 'name'
    _order = 'start_time'

    name = fields.Char(compute='_compute_name', store=True, readonly=True)
    shift_type = fields.Selection([
        ('morning', 'Morning'),
        ('day', 'Day'),
        ('evening', 'Evening'),
        ('night', 'Night'),
    ], string='Shift Type')
    start_time = fields.Float(string='Start Time', required=True)
    end_time = fields.Float(string='End Time', required=True)

    _sql_constraints = [
        ('end_after_start', 'CHECK(end_time > start_time)',
         'The shift must end after it starts.'),
    ]

    @api.depends('start_time', 'end_time')
    def _compute_name(self):
        for rec in self:
            rec.name = f'{rec.start_time:g} to {rec.end_time:g}'
