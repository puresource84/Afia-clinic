import re

from odoo import api, fields, models

# Tokens in the free-text alert that are noise, not substances.
_STOPWORDS = {
    'allergy', 'allergic', 'allergies', 'alert', 'alerts', 'severe', 'mild',
    'moderate', 'patient', 'history', 'known', 'reaction', 'avoid', 'with',
    'from', 'drug', 'drugs', 'therapy', 'diabetic', 'diabetes',
    'anticoagulant', 'pregnancy', 'pregnant', 'asthma', 'hypertension',
    'حساسية', 'تحسس', 'حساسيه', 'مريض', 'مريضة', 'دواء', 'أدوية', 'ادوية',
    'تجنب', 'شديدة', 'خفيفة', 'سكري', 'ضغط', 'حمل', 'ربو',
}

_TOKEN_RE = re.compile(r'[^\W\d_]{3,}', re.UNICODE)


class DentalAllergySubstance(models.Model):
    _name = 'dental.allergy.substance'
    _description = 'Allergy Substance (with cross-reactivity keywords)'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    keywords = fields.Char(
        string='Match Keywords',
        help='Comma-separated names/brands/cross-reactive drugs, EN + AR. '
             'A prescription medicine matching ANY keyword triggers the '
             'hard stop for patients allergic to this substance.')
    active = fields.Boolean(default=True)
    note = fields.Char(string='Clinical Note')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Substance already exists.'),
    ]

    def _keyword_set(self):
        self.ensure_one()
        kws = {k.strip().lower() for k in (self.keywords or '').split(',')
               if len(k.strip()) >= 3}
        kws.add((self.name or '').strip().lower())
        return kws


class DentalPatientAllergy(models.Model):
    _name = 'dental.patient.allergy'
    _description = 'Patient Allergy'
    _rec_name = 'substance_id'

    partner_id = fields.Many2one(
        'res.partner', string='Patient', required=True, ondelete='cascade',
        index=True, domain=[('is_patient', '=', True)])
    substance_id = fields.Many2one(
        'dental.allergy.substance', string='Substance', required=True,
        ondelete='restrict')
    severity = fields.Selection([
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    ], default='severe', required=True)
    reaction = fields.Char(string='Reaction',
                           help='e.g. rash, anaphylaxis, swelling')

    _sql_constraints = [
        ('partner_substance_uniq', 'unique(partner_id, substance_id)',
         'This allergy is already recorded for the patient.'),
    ]


class ResPartnerAllergyGuard(models.Model):
    _inherit = 'res.partner'

    allergy_ids = fields.One2many(
        'dental.patient.allergy', 'partner_id', string='Allergies')

    def _allergy_match_map(self):
        """Return {substance_label: set(keywords)} for this patient, built
        from the structured allergy list PLUS substances recognised inside
        the free-text alert (so the guard works before data migration)."""
        self.ensure_one()
        result = {}
        for line in self.allergy_ids.filtered(lambda l: l.substance_id.active):
            result.setdefault(line.substance_id.name,
                              set()).update(line.substance_id._keyword_set())
        free_text = (self.allergy_alert or '').lower()
        if free_text:
            tokens = {t for t in _TOKEN_RE.findall(free_text)
                      if t not in _STOPWORDS}
            if tokens:
                for substance in self.env['dental.allergy.substance'].sudo() \
                        .search([('active', '=', True)]):
                    kws = substance._keyword_set()
                    if any(tok in kw or kw in tok
                           for tok in tokens for kw in kws):
                        result.setdefault(substance.name, set()).update(kws)
                # Unrecognised tokens still match medicine names directly
                # (4+ chars to limit noise).
                direct = {t for t in tokens if len(t) >= 4}
                if direct:
                    result.setdefault('⚠ %s' % (self.allergy_alert or '')[:60],
                                      set()).update(direct)
        return result

    def _allergy_conflicts_for(self, medicine_names):
        """medicine_names: iterable of display strings to test.
        Returns list of (substance_label, medicine_name) conflicts."""
        self.ensure_one()
        conflicts = []
        match_map = self._allergy_match_map()
        for med in medicine_names:
            med_l = (med or '').lower()
            if not med_l:
                continue
            for substance, kws in match_map.items():
                if any(kw and kw in med_l for kw in kws):
                    conflicts.append((substance, med))
                    break
        return conflicts
