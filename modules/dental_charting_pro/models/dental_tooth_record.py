from odoo import api, fields, models
from odoo.osv import expression

# FDI two-digit notation: permanent (11-48) + deciduous/pediatric (51-85)
FDI_TEETH = [
    str(n) for quadrant in (10, 20, 30, 40) for n in range(quadrant + 1, quadrant + 9)
] + [
    str(n) for quadrant in (50, 60, 70, 80) for n in range(quadrant + 1, quadrant + 6)
]

CONDITIONS = [
    ('healthy', 'Healthy'),
    ('caries', 'Caries'),
    ('filled', 'Filled'),
    ('crown', 'Crown'),
    ('root_canal', 'Root Canal'),
    ('implant', 'Implant'),
    ('bridge', 'Bridge'),
    ('veneer', 'Veneer'),
    ('mobile', 'Mobility'),
    ('fractured', 'Fractured'),
    ('extracted', 'Extracted'),
    ('missing', 'Missing'),
]


class DentalToothRecord(models.Model):
    _name = 'dental.tooth.record'
    _description = 'Per-Tooth Clinical Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'record_date desc, id desc'
    _rec_name = 'display_label'

    patient_id = fields.Many2one(
        'res.partner', string='Patient', required=True, index=True,
        domain="[('is_patient', '=', True)]", ondelete='cascade')
    tooth_fdi = fields.Selection(
        [(t, t) for t in FDI_TEETH], string='Tooth (FDI)', required=True, index=True)
    condition = fields.Selection(
        CONDITIONS, string='Condition', required=True, default='healthy', tracking=True)
    # Tooth surfaces
    surface_mesial = fields.Boolean(string='Mesial (M)')
    surface_occlusal = fields.Boolean(string='Occlusal/Incisal (O)')
    surface_distal = fields.Boolean(string='Distal (D)')
    surface_buccal = fields.Boolean(string='Buccal/Labial (B)')
    surface_lingual = fields.Boolean(string='Lingual/Palatal (L)')

    appointment_id = fields.Many2one('dental.appointment', string='Appointment')
    treatment_id = fields.Many2one('dental.treatment', string='Treatment')
    doctor_id = fields.Many2one(
        'hr.employee', string='Doctor',
        domain="[('is_dentist', '=', True)]")
    record_date = fields.Date(string='Date', default=fields.Date.today, required=True)
    is_current = fields.Boolean(
        string='Current Status', default=True, index=True,
        help='Latest clinical status of this tooth. Older records form the history.')
    notes = fields.Text(string='Clinical Notes')
    display_label = fields.Char(compute='_compute_display_label', store=True)
    surfaces_label = fields.Char(compute='_compute_surfaces_label', string='Surfaces')

    @api.depends('tooth_fdi', 'condition', 'patient_id')
    def _compute_display_label(self):
        cond = dict(CONDITIONS)
        for rec in self:
            rec.display_label = '%s — Tooth %s (%s)' % (
                rec.patient_id.name or '', rec.tooth_fdi or '', cond.get(rec.condition, ''))

    @api.depends('surface_mesial', 'surface_occlusal', 'surface_distal',
                 'surface_buccal', 'surface_lingual')
    def _compute_surfaces_label(self):
        for rec in self:
            parts = []
            if rec.surface_mesial:
                parts.append('M')
            if rec.surface_occlusal:
                parts.append('O')
            if rec.surface_distal:
                parts.append('D')
            if rec.surface_buccal:
                parts.append('B')
            if rec.surface_lingual:
                parts.append('L')
            rec.surfaces_label = ''.join(parts)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # New record becomes the current status; demote previous ones.
        # Batched into a single OR'd search instead of one query per new
        # record, to avoid N+1 lookups when creating/importing many teeth
        # at once (e.g. bulk odontogram entry, migration hooks).
        new_current = records.filtered('is_current')
        if new_current:
            domain = expression.OR([
                [('patient_id', '=', rec.patient_id.id),
                 ('tooth_fdi', '=', rec.tooth_fdi),
                 ('id', '!=', rec.id),
                 ('is_current', '=', True)]
                for rec in new_current
            ])
            self.search(domain).write({'is_current': False})
        return records


class ResPartnerDental(models.Model):
    _inherit = 'res.partner'

    tooth_record_ids = fields.One2many(
        'dental.tooth.record', 'patient_id', string='Tooth Records')
    odontogram_data = fields.Json(
        compute='_compute_odontogram_data', string='Odontogram')
    tooth_record_count = fields.Integer(
        string='Dental Chart', compute='_compute_tooth_record_count')

    @api.depends('tooth_record_ids')
    def _compute_tooth_record_count(self):
        for partner in self:
            partner.tooth_record_count = len(partner.tooth_record_ids)

    def action_view_dental_chart(self):
        """Open the dedicated full-page Dental Chart view for this patient —
        the standalone page (chart + Print Chart button + full history list)
        that used to be reached only via the Appointment form's stat button.
        Restored 2026-08-24 as a stat button directly on the patient profile,
        matching how it worked before dental_charting_pro was refactored to
        the notebook-tab-only layout (see
        project_afia_odontogram_smart_button_restore memory)."""
        self.ensure_one()
        view = self.env.ref('dental_charting_pro.view_partner_form_dental_chart')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dental Chart',
            'res_model': 'res.partner',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'target': 'current',
        }

    @api.depends('tooth_record_ids.condition', 'tooth_record_ids.is_current',
                 'tooth_record_ids.surface_mesial', 'tooth_record_ids.surface_occlusal',
                 'tooth_record_ids.surface_distal', 'tooth_record_ids.surface_buccal',
                 'tooth_record_ids.surface_lingual')
    def _compute_odontogram_data(self):
        for partner in self:
            data = {}
            for rec in partner.tooth_record_ids.filtered('is_current'):
                surfaces = [
                    code for code, flag in (
                        ('M', rec.surface_mesial),
                        ('O', rec.surface_occlusal),
                        ('D', rec.surface_distal),
                        ('B', rec.surface_buccal),
                        ('L', rec.surface_lingual),
                    ) if flag
                ]
                data[rec.tooth_fdi] = {
                    'condition': rec.condition,
                    'surfaces': surfaces,
                }
            partner.odontogram_data = data
