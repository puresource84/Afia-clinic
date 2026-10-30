from odoo import fields, models, tools


class HrEmployeeCommission(models.Model):
    _inherit = 'hr.employee'

    commission_pct = fields.Float(
        string='Commission %', default=0.0,
        help='Percentage of production (sum of treatment costs of Done '
             'appointments) paid as commission to this dentist.')


class DentalCommissionReport(models.Model):
    """NEXT-bucket D2: monthly production & commission per dentist."""
    _name = 'dental.commission.report'
    _description = 'Dentist Commission Report'
    _auto = False
    _order = 'month desc, production desc'

    dentist_id = fields.Many2one('hr.employee', string='Dentist', readonly=True)
    month = fields.Date(string='Month', readonly=True)
    appointment_count = fields.Integer(string='Done Appointments', readonly=True)
    production = fields.Float(string='Production', readonly=True)
    commission_pct = fields.Float(string='Commission %', readonly=True)
    commission = fields.Float(string='Commission', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    a.dentist_id,
                    date_trunc('month', a.appointment_date)::date AS month,
                    count(DISTINCT a.id) AS appointment_count,
                    COALESCE(sum(t.cost), 0) AS production,
                    COALESCE(e.commission_pct, 0) AS commission_pct,
                    COALESCE(sum(t.cost), 0)
                        * COALESCE(e.commission_pct, 0) / 100.0 AS commission
                FROM dental_appointment a
                JOIN hr_employee e ON e.id = a.dentist_id
                LEFT JOIN dental_appointment_dental_treatment_rel r
                    ON r.dental_appointment_id = a.id
                LEFT JOIN dental_treatment t
                    ON t.id = r.dental_treatment_id
                WHERE a.state = 'done' AND a.dentist_id IS NOT NULL
                GROUP BY a.dentist_id,
                         date_trunc('month', a.appointment_date),
                         e.commission_pct
            )""" % self._table)
