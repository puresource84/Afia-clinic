"""
Tests for dental_perio_charting: exam creation, 28-tooth auto-seed,
stats computation (BOP%, avg PD, deep pocket counts), and sign-off lock.
"""
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPerioExam(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.patient = cls.env['res.partner'].create({
            'name': 'Perio Test Patient',
            'is_patient': True,
        })

    def _make_exam(self):
        return self.env['dental.perio.exam'].create({
            'patient_id': self.patient.id,
        })

    # ── Seeding ───────────────────────────────────────────────────────────────

    def test_28_readings_auto_created(self):
        exam = self._make_exam()
        self.assertEqual(len(exam.reading_ids), 28,
                         "Expected 28 tooth readings (no wisdom teeth)")

    def test_upper_lower_split(self):
        exam = self._make_exam()
        upper = exam.reading_ids.filtered(lambda r: r.arch == 'upper')
        lower = exam.reading_ids.filtered(lambda r: r.arch == 'lower')
        self.assertEqual(len(upper), 14)
        self.assertEqual(len(lower), 14)

    def test_fdi_numbers_correct(self):
        exam = self._make_exam()
        teeth = set(exam.reading_ids.mapped('tooth_number'))
        expected_upper = {'17','16','15','14','13','12','11','21','22','23','24','25','26','27'}
        expected_lower = {'47','46','45','44','43','42','41','31','32','33','34','35','36','37'}
        self.assertEqual(teeth, expected_upper | expected_lower)

    def test_no_duplicate_seed(self):
        """Creating a second exam must not double-seed the first."""
        exam1 = self._make_exam()
        self._make_exam()
        self.assertEqual(len(exam1.reading_ids), 28)

    # ── Stats ─────────────────────────────────────────────────────────────────

    def test_default_stats_all_2mm_no_bop(self):
        exam = self._make_exam()
        self.assertAlmostEqual(exam.avg_pd, 2.0, places=1)
        self.assertAlmostEqual(exam.bop_percent, 0.0, places=1)
        self.assertEqual(exam.pocket_4_count, 0)
        self.assertEqual(exam.pocket_6_count, 0)

    def test_stats_with_deep_pocket_and_bop(self):
        exam = self._make_exam()
        tooth16 = exam.reading_ids.filtered(lambda r: r.tooth_number == '16')
        # Set two bleeding sites and one deep pocket (7mm)
        tooth16.write({
            'mb_pd': 7, 'b_pd': 3, 'db_pd': 4,
            'ml_pd': 5, 'l_pd': 2, 'dl_pd': 3,
            'mb_bop': True, 'db_bop': True,
        })
        # Trigger recompute
        exam._compute_stats()
        # BOP: 2 sites / (28*6=168 total) * 100 ≈ 1.19%
        self.assertAlmostEqual(exam.bop_percent, 2 / 168 * 100, places=1)
        # Pockets ≥4: 7,4,5 on tooth16 → 3
        self.assertEqual(exam.pocket_4_count, 3)
        # Pockets ≥6: 7 → 1
        self.assertEqual(exam.pocket_6_count, 1)

    def test_avg_pd_single_tooth_edit(self):
        exam = self._make_exam()
        tooth11 = exam.reading_ids.filtered(lambda r: r.tooth_number == '11')
        # Change all 6 sites on tooth 11 to 4mm (default 2mm everywhere else)
        tooth11.write({
            'mb_pd': 4, 'b_pd': 4, 'db_pd': 4,
            'ml_pd': 4, 'l_pd': 4, 'dl_pd': 4,
        })
        exam._compute_stats()
        # 27 teeth * 6 * 2 + 1 tooth * 6 * 4 = 324 + 24 = 348; /168 = 2.071
        # avg_pd stored with digits=(5,1) → rounds to 2.1; compare at 1 decimal
        expected = (27 * 6 * 2 + 6 * 4) / 168
        self.assertAlmostEqual(exam.avg_pd, expected, places=1)

    # ── Sign-off ──────────────────────────────────────────────────────────────

    def test_sign_sets_state(self):
        exam = self._make_exam()
        self.assertEqual(exam.state, 'draft')
        exam.action_sign()
        self.assertEqual(exam.state, 'signed')

    def test_reset_to_draft(self):
        exam = self._make_exam()
        exam.action_sign()
        exam.action_reset_draft()
        self.assertEqual(exam.state, 'draft')

    # ── Missing tooth ─────────────────────────────────────────────────────────

    def test_missing_tooth_excluded_from_avg(self):
        """A missing tooth's readings should not inflate the PD average."""
        exam = self._make_exam()
        tooth17 = exam.reading_ids.filtered(lambda r: r.tooth_number == '17')
        tooth17.write({'is_missing': True,
                       'mb_pd': 9, 'b_pd': 9, 'db_pd': 9,
                       'ml_pd': 9, 'l_pd': 9, 'dl_pd': 9})
        exam._compute_stats()
        # Missing tooth should be excluded → avg stays at 2.0
        self.assertAlmostEqual(exam.avg_pd, 2.0, places=1)
