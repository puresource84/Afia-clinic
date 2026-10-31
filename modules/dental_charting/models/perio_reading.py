"""
dental.perio.reading — one row per tooth per exam.

Records 6-point probing data:
  Buccal side  — Mesio-Buccal (MB), Buccal (B), Disto-Buccal (DB)
  Lingual side — Mesio-Lingual (ML), Lingual (L), Disto-Lingual (DL)

Each point stores:
  PD  — Pocket Depth in mm  (integer 1–12)
  REC — Recession in mm     (integer, 0 = gingival margin at CEJ)
  BOP — Bleeding on Probing (boolean)

Clinical Attachment Level (CAL) = PD + REC (computed).
"""
from odoo import api, fields, models


class DentalPerioReading(models.Model):
    _name = 'dental.perio.reading'
    _description = 'Periodontal Reading (per tooth)'
    _order = 'arch, tooth_number'

    exam_id = fields.Many2one(
        'dental.perio.exam', required=True,
        ondelete='cascade', index=True)

    tooth_number = fields.Char(
        string='Tooth', required=True,
        help='FDI tooth number (e.g. 16, 24, 36)')

    arch = fields.Selection([
        ('upper', 'Upper'),
        ('lower', 'Lower'),
    ], required=True, default='upper')

    is_missing = fields.Boolean(
        string='Missing',
        help='Tooth is absent — skip probing.')

    mobility = fields.Selection([
        ('0', '0'), ('1', 'I'), ('2', 'II'), ('3', 'III'),
    ], string='Mob', default='0',
       help='Tooth mobility: 0 = none, I–III = increasing mobility.')

    furcation = fields.Selection([
        ('0', 'None'), ('1', 'I'), ('2', 'II'), ('3', 'III'),
    ], string='Furc', default='0',
       help='Furcation involvement class (multi-rooted teeth).')

    # ── Buccal / Facial ───────────────────────────────────────────────────────
    mb_pd  = fields.Integer('MB PD',  default=2)
    b_pd   = fields.Integer('B PD',   default=2)
    db_pd  = fields.Integer('DB PD',  default=2)

    mb_rec = fields.Integer('MB Rec', default=0)
    b_rec  = fields.Integer('B Rec',  default=0)
    db_rec = fields.Integer('DB Rec', default=0)

    mb_bop = fields.Boolean('MB BOP')
    b_bop  = fields.Boolean('B BOP')
    db_bop = fields.Boolean('DB BOP')

    # ── Lingual / Palatal ─────────────────────────────────────────────────────
    ml_pd  = fields.Integer('ML PD',  default=2)
    l_pd   = fields.Integer('L PD',   default=2)
    dl_pd  = fields.Integer('DL PD',  default=2)

    ml_rec = fields.Integer('ML Rec', default=0)
    l_rec  = fields.Integer('L Rec',  default=0)
    dl_rec = fields.Integer('DL Rec', default=0)

    ml_bop = fields.Boolean('ML BOP')
    l_bop  = fields.Boolean('L BOP')
    dl_bop = fields.Boolean('DL BOP')

    # ── Computed summaries ────────────────────────────────────────────────────
    max_pd = fields.Integer(
        compute='_compute_derived', store=True,
        string='Max PD',
        help='Highest pocket depth on this tooth (all 6 sites).')

    bop_count = fields.Integer(
        compute='_compute_derived', store=True,
        string='BOP Sites',
        help='Number of probing sites that bled (0–6).')

    mb_cal = fields.Integer(compute='_compute_derived', store=True, string='MB CAL')
    b_cal  = fields.Integer(compute='_compute_derived', store=True, string='B CAL')
    db_cal = fields.Integer(compute='_compute_derived', store=True, string='DB CAL')
    ml_cal = fields.Integer(compute='_compute_derived', store=True, string='ML CAL')
    l_cal  = fields.Integer(compute='_compute_derived', store=True, string='L CAL')
    dl_cal = fields.Integer(compute='_compute_derived', store=True, string='DL CAL')

    @api.depends(
        'mb_pd', 'b_pd', 'db_pd', 'ml_pd', 'l_pd', 'dl_pd',
        'mb_rec', 'b_rec', 'db_rec', 'ml_rec', 'l_rec', 'dl_rec',
        'mb_bop', 'b_bop', 'db_bop', 'ml_bop', 'l_bop', 'dl_bop',
    )
    def _compute_derived(self):
        for r in self:
            pds = [r.mb_pd, r.b_pd, r.db_pd, r.ml_pd, r.l_pd, r.dl_pd]
            r.max_pd = max(pds) if any(pds) else 0
            r.bop_count = sum([
                r.mb_bop, r.b_bop, r.db_bop,
                r.ml_bop, r.l_bop, r.dl_bop,
            ])
            r.mb_cal = r.mb_pd + r.mb_rec
            r.b_cal  = r.b_pd  + r.b_rec
            r.db_cal = r.db_pd + r.db_rec
            r.ml_cal = r.ml_pd + r.ml_rec
            r.l_cal  = r.l_pd  + r.l_rec
            r.dl_cal = r.dl_pd + r.dl_rec
