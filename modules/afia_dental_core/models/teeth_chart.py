# -*- coding: utf-8 -*-
"""Legacy flat tooth chart (one boolean per tooth). Superseded by the
proper FDI odontogram in dental_charting_pro (dental.tooth.record) —
kept here only because one companion module still references it.
Do not build new features against this model."""
from odoo import api, fields, models

TOOTH_COUNT = 32


class TeethChart(models.Model):
    _name = 'teeth.chart'
    _description = 'Teeth Chart Record (legacy)'

    name = fields.Char(string='Patient Name', required=True)
    selected_teeth = fields.Char(compute='_compute_selected_teeth', store=True)

    tooth_1 = fields.Boolean(string='Tooth 1')
    tooth_2 = fields.Boolean(string='Tooth 2')
    tooth_3 = fields.Boolean(string='Tooth 3')
    tooth_4 = fields.Boolean(string='Tooth 4')
    tooth_5 = fields.Boolean(string='Tooth 5')
    tooth_6 = fields.Boolean(string='Tooth 6')
    tooth_7 = fields.Boolean(string='Tooth 7')
    tooth_8 = fields.Boolean(string='Tooth 8')
    tooth_9 = fields.Boolean(string='Tooth 9')
    tooth_10 = fields.Boolean(string='Tooth 10')
    tooth_11 = fields.Boolean(string='Tooth 11')
    tooth_12 = fields.Boolean(string='Tooth 12')
    tooth_13 = fields.Boolean(string='Tooth 13')
    tooth_14 = fields.Boolean(string='Tooth 14')
    tooth_15 = fields.Boolean(string='Tooth 15')
    tooth_16 = fields.Boolean(string='Tooth 16')
    tooth_17 = fields.Boolean(string='Tooth 17')
    tooth_18 = fields.Boolean(string='Tooth 18')
    tooth_19 = fields.Boolean(string='Tooth 19')
    tooth_20 = fields.Boolean(string='Tooth 20')
    tooth_21 = fields.Boolean(string='Tooth 21')
    tooth_22 = fields.Boolean(string='Tooth 22')
    tooth_23 = fields.Boolean(string='Tooth 23')
    tooth_24 = fields.Boolean(string='Tooth 24')
    tooth_25 = fields.Boolean(string='Tooth 25')
    tooth_26 = fields.Boolean(string='Tooth 26')
    tooth_27 = fields.Boolean(string='Tooth 27')
    tooth_28 = fields.Boolean(string='Tooth 28')
    tooth_29 = fields.Boolean(string='Tooth 29')
    tooth_30 = fields.Boolean(string='Tooth 30')
    tooth_31 = fields.Boolean(string='Tooth 31')
    tooth_32 = fields.Boolean(string='Tooth 32')

    @api.depends(*[f'tooth_{i}' for i in range(1, TOOTH_COUNT + 1)])
    def _compute_selected_teeth(self):
        for rec in self:
            selected = [str(i) for i in range(1, TOOTH_COUNT + 1) if rec[f'tooth_{i}']]
            rec.selected_teeth = ', '.join(f'Tooth-{i}' for i in selected) if selected else 'None'
