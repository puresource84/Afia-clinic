"""
dental.perio.exam — one periodontal examination per patient per visit.

Standard perio chart: 6-point probing (MB, B, DB buccal + ML, L, DL lingual)
per tooth for pocket depth (PD), recession (REC), and bleeding on probing (BOP).
28 tooth readings are auto-created when an exam record is first saved.
"""
from odoo import api, fields, models

# FDI tooth numbers for default perio chart (no wisdom teeth)
_UPPER_TEETH = ['17', '16', '15', '14', '13', '12', '11',
                '21', '22', '23', '24', '25', '26', '27']
_LOWER_TEETH = ['47', '46', '45', '44', '43', '42', '41',
                '31', '32', '33', '34', '35', '36', '37']
_ALL_TEETH = _UPPER_TEETH + _LOWER_TEETH


class DentalPerioExam(models.Model):
    _name = 'dental.perio.exam'
    _description = 'Periodontal Examination'
    _order = 'exam_date desc, id desc'
    _rec_name = 'display_name'

    # ── Identity ──────────────────────────────────────────────────────────────
    display_name = fields.Char(compute='_compute_display_name', store=True)

    patient_id = fields.Many2one(
        'res.partner', string='Patient', required=True,
        domain="[('is_patient', '=', True)]",
        index=True, tracking=True)

    appointment_id = fields.Many2one(
        'dental.appointment', string='Appointment',
        domain="[('patient_id', '=', patient_id)]",
        tracking=True)

    dentist_id = fields.Many2one(
        'res.users', string='Dentist',
        default=lambda self: self.env.user, tracking=True)

    exam_date = fields.Date(
        string='Exam Date', required=True,
        default=fields.Date.today, index=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('signed', 'Signed'),
    ], default='draft', string='Status', tracking=True)

    notes = fields.Text(string='Clinical Notes')

    # ── Readings ──────────────────────────────────────────────────────────────
    reading_ids = fields.One2many(
        'dental.perio.reading', 'exam_id', string='Tooth Readings')

    upper_reading_ids = fields.One2many(
        'dental.perio.reading', 'exam_id',
        string='Upper Arch',
        domain=[('arch', '=', 'upper')])

    lower_reading_ids = fields.One2many(
        'dental.perio.reading', 'exam_id',
        string='Lower Arch',
        domain=[('arch', '=', 'lower')])

    # ── Summary stats ─────────────────────────────────────────────────────────
    bop_percent = fields.Float(
        compute='_compute_stats', store=True,
        string='BOP %', digits=(5, 1),
        help='Percentage of probing sites that bled.')

    avg_pd = fields.Float(
        compute='_compute_stats', store=True,
        string='Avg PD (mm)', digits=(5, 1))

    pocket_4_count = fields.Integer(
        compute='_compute_stats', store=True,
        string='Pockets ≥ 4 mm')

    pocket_6_count = fields.Integer(
        compute='_compute_stats', store=True,
        string='Pockets ≥ 6 mm')

    # ── Historical comparison ─────────────────────────────────────────────────
    prev_exam_id = fields.Many2one(
        'dental.perio.exam',
        compute='_compute_prev_exam',
        string='Previous Exam')

    prev_exam_date = fields.Date(
        related='prev_exam_id.exam_date',
        string='Prev Exam Date')

    prev_bop_percent = fields.Float(
        related='prev_exam_id.bop_percent',
        string='Prev BOP %', digits=(5, 1))

    prev_avg_pd = fields.Float(
        related='prev_exam_id.avg_pd',
        string='Prev Avg PD', digits=(5, 1))

    # ── Sign-off ──────────────────────────────────────────────────────────────
    signed_by = fields.Many2one('res.users', string='Signed By', readonly=True)
    signed_date = fields.Datetime(string='Signed Date', readonly=True)

    # ── Compute ───────────────────────────────────────────────────────────────
    @api.depends('patient_id', 'exam_date')
    def _compute_display_name(self):
        for rec in self:
            pt = rec.patient_id.name or ''
            dt = rec.exam_date or ''
            rec.display_name = f'Perio — {pt} — {dt}' if pt else 'Perio Exam'

    @api.depends('reading_ids.mb_pd', 'reading_ids.b_pd', 'reading_ids.db_pd',
                 'reading_ids.ml_pd', 'reading_ids.l_pd', 'reading_ids.dl_pd',
                 'reading_ids.mb_bop', 'reading_ids.b_bop', 'reading_ids.db_bop',
                 'reading_ids.ml_bop', 'reading_ids.l_bop', 'reading_ids.dl_bop',
                 'reading_ids.is_missing')
    def _compute_stats(self):
        for exam in self:
            active = exam.reading_ids.filtered(lambda r: not r.is_missing)
            if not active:
                exam.bop_percent = 0.0
                exam.avg_pd = 0.0
                exam.pocket_4_count = 0
                exam.pocket_6_count = 0
                continue

            all_pd = []
            bop_count = 0
            site_count = 0
            p4 = p6 = 0

            for r in active:
                pds = [r.mb_pd, r.b_pd, r.db_pd, r.ml_pd, r.l_pd, r.dl_pd]
                bops = [r.mb_bop, r.b_bop, r.db_bop, r.ml_bop, r.l_bop, r.dl_bop]
                all_pd.extend(pds)
                bop_count += sum(bops)
                site_count += 6
                p4 += sum(1 for p in pds if p >= 4)
                p6 += sum(1 for p in pds if p >= 6)

            exam.bop_percent = (bop_count / site_count * 100) if site_count else 0.0
            exam.avg_pd = (sum(all_pd) / len(all_pd)) if all_pd else 0.0
            exam.pocket_4_count = p4
            exam.pocket_6_count = p6

    @api.depends('patient_id', 'exam_date')
    def _compute_prev_exam(self):
        for exam in self:
            prev = self.search([
                ('patient_id', '=', exam.patient_id.id),
                ('exam_date', '<', exam.exam_date or fields.Date.today()),
                ('id', '!=', exam.id),
            ], order='exam_date desc', limit=1)
            exam.prev_exam_id = prev

    # ── ORM ───────────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.reading_ids:
                rec._create_default_readings()
        return records

    def _create_default_readings(self):
        Reading = self.env['dental.perio.reading']
        vals = []
        for tooth in _UPPER_TEETH:
            vals.append({'exam_id': self.id, 'tooth_number': tooth, 'arch': 'upper'})
        for tooth in _LOWER_TEETH:
            vals.append({'exam_id': self.id, 'tooth_number': tooth, 'arch': 'lower'})
        Reading.create(vals)

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_sign(self):
        self.ensure_one()
        self.write({
            'state': 'signed',
            'signed_by': self.env.uid,
            'signed_date': fields.Datetime.now(),
        })

    def action_reset_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
