from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestToothRecord(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.patient = cls.env['res.partner'].create({
            'name': 'Test Patient', 'is_patient': True})

    def _rec(self, fdi='11', condition='caries', **kw):
        vals = {'patient_id': self.patient.id, 'tooth_fdi': fdi,
                'condition': condition}
        vals.update(kw)
        return self.env['dental.tooth.record'].create(vals)

    def test_create_sets_current(self):
        rec = self._rec()
        self.assertTrue(rec.is_current)
        self.assertIn('Tooth 11', rec.display_label)

    def test_new_record_demotes_previous(self):
        old = self._rec(condition='caries')
        new = self._rec(condition='filled')
        self.assertFalse(old.is_current, 'previous record must lose current flag')
        self.assertTrue(new.is_current)

    def test_other_tooth_not_demoted(self):
        t11 = self._rec(fdi='11')
        t12 = self._rec(fdi='12')
        self.assertTrue(t11.is_current)
        self.assertTrue(t12.is_current)

    def test_surfaces_label(self):
        rec = self._rec(surface_mesial=True, surface_occlusal=True,
                        surface_lingual=True)
        self.assertEqual(rec.surfaces_label, 'MOL')

    def test_odontogram_data_reflects_current(self):
        self._rec(fdi='21', condition='caries')
        self._rec(fdi='21', condition='root_canal')
        data = self.patient.odontogram_data
        self.assertEqual(data.get('21'), 'root_canal',
                         'odontogram must show latest current condition')

    def test_history_preserved(self):
        self._rec(fdi='36', condition='caries')
        self._rec(fdi='36', condition='filled')
        recs = self.env['dental.tooth.record'].search([
            ('patient_id', '=', self.patient.id), ('tooth_fdi', '=', '36')])
        self.assertEqual(len(recs), 2, 'history must be preserved')
