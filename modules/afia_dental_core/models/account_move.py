# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_treatment_invoice = fields.Boolean(string='Treatment Invoice', default=False)
