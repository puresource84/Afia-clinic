import math

from odoo import models

# Kept in sync by hand with CONDITION_COLORS in
# static/src/odontogram/odontogram.js — the printed chart must use the same
# palette as the interactive widget so a dentist recognizes it at a glance.
CONDITION_COLORS = {
    'healthy': '#ffffff',
    'caries': '#ef5350',
    'filled': '#42a5f5',
    'crown': '#ffb300',
    'root_canal': '#ff8a00',
    'implant': '#26a69a',
    'bridge': '#8d6e63',
    'veneer': '#ec407a',
    'mobile': '#fdd835',
    'fractured': '#ff7043',
    'extracted': '#7e57c2',
    'missing': '#7e57c2',
}

# Adult (permanent) FDI layout — matches the widget's default "Adult" view.
UPPER = ['18', '17', '16', '15', '14', '13', '12', '11',
         '21', '22', '23', '24', '25', '26', '27', '28']
LOWER = ['48', '47', '46', '45', '44', '43', '42', '41',
         '31', '32', '33', '34', '35', '36', '37', '38']

# Pediatric (deciduous/primary) FDI layout — mirrors UPPER_DECID/LOWER_DECID
# in odontogram.js so the printed chart always shows both dentitions
# regardless of the patient's actual mixed-dentition state.
UPPER_DECID = ['55', '54', '53', '52', '51', '61', '62', '63', '64', '65']
LOWER_DECID = ['85', '84', '83', '82', '81', '71', '72', '73', '74', '75']


class ResPartnerDentalPrint(models.Model):
    _inherit = 'res.partner'

    def _dental_print_regions(self, fdi, arch, data):
        """Per-surface fill colors for one tooth, oriented the same way as
        toothRegions() in odontogram.js (top/right/bottom/left/center)."""
        info = data.get(fdi) or {}
        condition = info.get('condition')
        surfaces = info.get('surfaces') or []
        cond_color = CONDITION_COLORS.get(condition, '#ffffff')
        whole_tooth = bool(condition) and not surfaces

        quadrant = fdi[0]
        mesial_right = quadrant in ('1', '4')
        buccal_top = arch == 'upper'
        top_key = 'B' if buccal_top else 'L'
        bottom_key = 'L' if buccal_top else 'B'
        right_key = 'M' if mesial_right else 'D'
        left_key = 'D' if mesial_right else 'M'

        def fill(code):
            return cond_color if (whole_tooth or code in surfaces) else '#ffffff'

        return {
            'top': fill(top_key),
            'right': fill(right_key),
            'bottom': fill(bottom_key),
            'left': fill(left_key),
            'center': fill('O'),
        }

    def _dental_print_teeth(self, pediatric=False):
        """Ring layout data for the printable chart: same ellipse placement
        math as ringTeeth() in odontogram.js, computed server-side so it can
        be rendered as static SVG in a QWeb PDF report (no JS at print
        time). Pass pediatric=True to lay out the deciduous arches instead
        of the permanent ones."""
        self.ensure_one()
        cx, cy, rx, ry = 150, 170, 110, 140
        data = self.odontogram_data or {}
        upper_arr = UPPER_DECID if pediatric else UPPER
        lower_arr = LOWER_DECID if pediatric else LOWER

        def place(arr, arch):
            step = 150.0 / max(len(arr) - 1, 1)
            teeth = []
            for i, fdi in enumerate(arr):
                angle = (195 + step * i) if arch == 'upper' else (165 - step * i)
                rad = math.radians(angle)
                teeth.append({
                    'fdi': fdi,
                    'x': cx + rx * math.cos(rad),
                    'y': cy + ry * math.sin(rad),
                    'regions': self._dental_print_regions(fdi, arch, data),
                })
            return teeth

        return place(upper_arr, 'upper') + place(lower_arr, 'lower')

    def _dental_print_legend(self):
        return [
            (code, code.replace('_', ' ').title(), color)
            for code, color in CONDITION_COLORS.items() if code != 'healthy'
        ]

    def _dental_print_dentitions(self):
        """Which arch(es) to print, decided from what was actually charted
        rather than a fixed patient flag (none exists yet — see
        odoo-dev-loop-gotchas memory). If the dentist recorded any adult FDI
        codes, include the adult ring; any deciduous codes, include the
        pediatric ring. A patient charted only as an adult prints one page;
        a mixed-dentition patient charted in both prints both. If nothing
        has been charted yet, default to adult only so the report isn't
        blank."""
        self.ensure_one()
        data = self.odontogram_data or {}
        charted = set(data.keys())
        adult_fdis = set(UPPER) | set(LOWER)
        decid_fdis = set(UPPER_DECID) | set(LOWER_DECID)

        has_adult = bool(charted & adult_fdis)
        has_pediatric = bool(charted & decid_fdis)
        if not has_adult and not has_pediatric:
            has_adult = True

        dentitions = []
        if has_adult:
            dentitions.append({
                'label': 'Permanent Dentition (Adult)',
                'pediatric': False,
                'teeth': self._dental_print_teeth(pediatric=False),
            })
        if has_pediatric:
            dentitions.append({
                'label': 'Primary Dentition (Pediatric)',
                'pediatric': True,
                'teeth': self._dental_print_teeth(pediatric=True),
            })
        return dentitions
