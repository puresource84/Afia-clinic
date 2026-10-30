from lxml import etree

from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestReceptionistAccess(TransactionCase):
    """Front-desk staff must be able to register and open patients even
    though this module strips clinical-model rights from plain internal
    users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['medical.questions'].create({'question': 'Any allergies?'})
        cls.receptionist = new_test_user(
            cls.env, login='afia_reception_test',
            groups='clinic_core.group_clinic_receptionist')

    def test_receptionist_can_create_patient(self):
        Partner = self.env['res.partner'].with_user(self.receptionist)
        patient = Partner.create({'name': 'Walk-in Patient', 'is_patient': True})
        self.assertTrue(patient.patient_no)
        rows = self.env['medical.questionnaire'].search(
            [('patient_id', '=', patient.id)])
        self.assertTrue(rows, 'questionnaire rows are still seeded')

    def test_receptionist_can_open_patient_form(self):
        patient = self.env['res.partner'].create(
            {'name': 'Existing Patient', 'is_patient': True})
        Partner = self.env['res.partner'].with_user(self.receptionist)
        arch = Partner.get_views([(False, 'form')])['views']['form']['arch']
        self.assertNotIn('report_ids', arch,
                         'X-Ray tab must be hidden from receptionists')
        # Read what the web client reads: the form's own (non-subview) fields.
        root = etree.fromstring(arch)
        names = {
            node.get('name') for node in root.iter('field')
            if not any(a.tag == 'field' for a in node.iterancestors())
        }
        Partner.browse(patient.id).read(sorted(names))
