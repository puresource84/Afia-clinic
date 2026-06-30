import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DentalTreatmentConsumable(models.Model):
    """Bill of materials line: what one execution of a treatment consumes."""
    _name = 'dental.treatment.consumable'
    _description = 'Treatment Consumable Line'

    treatment_id = fields.Many2one(
        'dental.treatment', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string='Material', required=True,
        domain="[('type', 'in', ('consu', 'product'))]")
    quantity = fields.Float(string='Qty / Procedure', default=1.0)
    uom_id = fields.Many2one(related='product_id.uom_id', string='Unit')
    standard_cost = fields.Float(
        related='product_id.standard_price', string='Unit Cost')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._flag_products_as_consumable(records.mapped('product_id'))
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'product_id' in vals:
            self._flag_products_as_consumable(self.mapped('product_id'))
        return res

    @api.model
    def _flag_products_as_consumable(self, products):
        """Mark products as clinic consumables so they appear in Clinic Stock."""
        if products:
            products.filtered(lambda p: not p.is_clinic_consumable).write(
                {'is_clinic_consumable': True})


class DentalTreatmentBom(models.Model):
    _inherit = 'dental.treatment'

    consumable_line_ids = fields.One2many(
        'dental.treatment.consumable', 'treatment_id',
        string='Consumed Materials')
    material_cost = fields.Float(
        string='Material Cost', compute='_compute_material_cost')

    @api.depends('consumable_line_ids.quantity',
                 'consumable_line_ids.product_id.standard_price')
    def _compute_material_cost(self):
        for treatment in self:
            treatment.material_cost = sum(
                l.quantity * l.product_id.standard_price
                for l in treatment.consumable_line_ids)


class DentalAppointmentConsume(models.Model):
    _inherit = 'dental.appointment'

    consumption_move_ids = fields.One2many(
        'stock.move', 'dental_appointment_id', string='Material Moves')
    material_cost = fields.Float(
        string='Materials Used', compute='_compute_material_cost')

    def _compute_material_cost(self):
        for apt in self:
            apt.material_cost = sum(
                t.material_cost for t in apt.treatments)

    def action_done(self):
        res = super().action_done()
        for apt in self:
            try:
                apt._consume_treatment_materials()
            except Exception as exc:  # noqa: BLE001 — never block Done
                _logger.warning(
                    'Material consumption failed for %s: %s',
                    apt.appointment_no, exc)
                apt.message_post(
                    body='⚠ Material consumption could not be recorded '
                         'automatically: %s' % exc)
        return res

    def _consume_treatment_materials(self):
        self.ensure_one()
        if self.consumption_move_ids:
            return  # already consumed
        lines = self.treatments.mapped('consumable_line_ids')
        if not lines:
            return
        # Company-filtered: on shared/multi-company DBs an unfiltered search
        # returns another company's location → "Incompatible companies"
        # crash → move stuck in 'confirmed' (root cause of Omar's finding).
        company = self.env.company
        Location = self.env['stock.location']
        src = Location.search([
            ('usage', '=', 'internal'),
            ('company_id', '=', company.id)], limit=1)
        dest = Location.search([
            ('usage', '=', 'production'),
            ('company_id', '=', company.id)], limit=1) or \
            Location.search([
                ('usage', '=', 'customer'),
                ('company_id', 'in', (company.id, False))], limit=1)
        if not (src and dest):
            return
        moves = self.env['stock.move']
        for line in lines:
            move = self.env['stock.move'].create({
                'name': '%s / %s' % (self.appointment_no or 'APT',
                                     line.product_id.display_name),
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.quantity,
                'location_id': src.id,
                'location_dest_id': dest.id,
                'dental_appointment_id': self.id,
                'company_id': self.env.company.id,
            })
            move._action_confirm()
            # Explicit move lines: do NOT rely on the `quantity` inverse —
            # it can leave the move stuck in 'confirmed' (QA finding,
            # Omar follow-up 2026-06-12).
            move.move_line_ids.unlink()
            self.env['stock.move.line'].create({
                'move_id': move.id,
                'product_id': move.product_id.id,
                'product_uom_id': move.product_uom.id,
                'quantity': line.quantity,
                'location_id': move.location_id.id,
                'location_dest_id': move.location_dest_id.id,
                'company_id': move.company_id.id,
            })
            move.picked = True
            moves |= move
        moves._action_done()
        stuck = moves.filtered(lambda m: m.state != 'done')
        if stuck:
            _logger.warning(
                'Consumption moves not done for %s: %s (states: %s)',
                self.appointment_no, stuck.ids, stuck.mapped('state'))
            self.message_post(
                body='⚠ %d material move(s) did not reach Done state — '
                     'check stock configuration.' % len(stuck))
        self.message_post(
            body='Materials consumed for %d treatment line(s) '
                 '(stock updated).' % len(lines))


class StockMoveDental(models.Model):
    _inherit = 'stock.move'

    dental_appointment_id = fields.Many2one(
        'dental.appointment', string='Dental Appointment', index=True)


class DentalProductConsumable(models.Model):
    """Extends product.product with a stored flag so the Clinic Stock view can
    filter to only clinic materials — whether added via a treatment BOM or
    flagged manually by staff."""
    _inherit = 'product.product'

    is_clinic_consumable = fields.Boolean(
        string='Clinic Consumable',
        default=False,
        store=True,
        copy=True,
        help="When checked, this product appears in the Clinic Stock view. "
             "Set automatically when the product is added to any treatment BOM. "
             "Can also be set manually for general clinic supplies.",
    )
