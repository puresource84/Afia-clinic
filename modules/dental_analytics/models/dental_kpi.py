from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta


class DentalKpi(models.Model):
    _name = 'dental.kpi'
    _description = 'Dental Clinic KPI Snapshot'
    _order = 'date desc'
    _rec_name = 'date'

    date = fields.Date(default=fields.Date.today, required=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    # Appointment metrics
    total_appointments = fields.Integer(string='Total Appointments')
    completed_appointments = fields.Integer(string='Completed')
    cancelled_appointments = fields.Integer(string='Cancelled')
    no_show_count = fields.Integer(string='No-Shows')
    completion_rate = fields.Float(string='Completion Rate %',
        compute='_compute_rates', store=True)
    cancellation_rate = fields.Float(string='Cancellation Rate %',
        compute='_compute_rates', store=True)

    # Patient metrics
    new_patients = fields.Integer(string='New Patients This Month')
    total_active_patients = fields.Integer(string='Total Active Patients')

    # Revenue
    total_revenue = fields.Float(string='Total Revenue')
    revenue_per_dentist = fields.Float(string='Avg Revenue / Dentist')

    @api.depends('total_appointments', 'completed_appointments', 'cancelled_appointments')
    def _compute_rates(self):
        for r in self:
            total = r.total_appointments or 1
            r.completion_rate = r.completed_appointments / total * 100
            r.cancellation_rate = r.cancelled_appointments / total * 100

    @api.model
    def compute_snapshot(self):
        """Called by cron or manually to store a fresh KPI snapshot."""
        today = date.today()
        month_start = today.replace(day=1)

        appts = self.env['dental.appointment'].search([
            ('appointment_date', '>=', str(month_start)),
            ('appointment_date', '<=', str(today)),
        ])
        total = len(appts)
        done = len(appts.filtered(lambda a: a.state == 'done'))
        cancelled = len(appts.filtered(lambda a: a.state == 'cancelled'))

        new_pts = self.env['res.partner'].search_count([
            ('is_patient', '=', True),
            ('create_date', '>=', str(month_start)),
        ])
        total_pts = self.env['res.partner'].search_count([('is_patient', '=', True)])

        dentists = self.env['hr.employee'].search([('is_dentist', '=', True)])
        dentist_count = len(dentists) or 1

        payments = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', str(month_start)),
        ])
        revenue = sum(payments.mapped('amount_total'))

        snap = self.create({
            'date': today,
            'total_appointments': total,
            'completed_appointments': done,
            'cancelled_appointments': cancelled,
            'new_patients': new_pts,
            'total_active_patients': total_pts,
            'total_revenue': revenue,
            'revenue_per_dentist': revenue / dentist_count,
        })
        return snap

    def action_compute_now(self):
        return self.compute_snapshot()