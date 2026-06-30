from odoo import models, fields,api


class TeethChart(models.Model):
    _name = "teeth.chart"
    _description = "Teeth Chart Record"

    name = fields.Char(string="Patient Name", required=True)

    # Fields for each tooth (Boolean to indicate selection)
    tooth_1 = fields.Boolean(string="Tooth 1")
    tooth_2 = fields.Boolean(string="Tooth 2")
    tooth_3 = fields.Boolean(string="Tooth 3")
    tooth_4 = fields.Boolean(string="Tooth 4")
    tooth_5 = fields.Boolean(string="Tooth 5")
    tooth_6 = fields.Boolean(string="Tooth 6")
    tooth_7 = fields.Boolean(string="Tooth 7")
    tooth_8 = fields.Boolean(string="Tooth 8")
    tooth_9 = fields.Boolean(string="Tooth 9")
    tooth_10 = fields.Boolean(string="Tooth 10")
    tooth_11 = fields.Boolean(string="Tooth 11")
    tooth_12 = fields.Boolean(string="Tooth 12")
    tooth_13 = fields.Boolean(string="Tooth 13")
    tooth_14 = fields.Boolean(string="Tooth 14")
    tooth_15 = fields.Boolean(string="Tooth 15")
    tooth_16 = fields.Boolean(string="Tooth 16")
    tooth_17 = fields.Boolean(string="Tooth 17")
    tooth_18 = fields.Boolean(string="Tooth 18")
    tooth_19 = fields.Boolean(string="Tooth 19")
    tooth_20 = fields.Boolean(string="Tooth 20")
    tooth_21 = fields.Boolean(string="Tooth 21")
    tooth_22 = fields.Boolean(string="Tooth 22")
    tooth_23 = fields.Boolean(string="Tooth 23")
    tooth_24 = fields.Boolean(string="Tooth 24")
    tooth_25 = fields.Boolean(string="Tooth 25")
    tooth_26 = fields.Boolean(string="Tooth 26")
    tooth_27 = fields.Boolean(string="Tooth 27")
    tooth_28 = fields.Boolean(string="Tooth 28")
    tooth_29 = fields.Boolean(string="Tooth 29")
    tooth_30 = fields.Boolean(string="Tooth 30")
    tooth_31 = fields.Boolean(string="Tooth 31")
    tooth_32 = fields.Boolean(string="Tooth 32")

    selected_teeth = fields.Char(string="Selected Teeth", compute="_compute_selected_teeth", store=True)

    @api.depends(
        'tooth_1', 'tooth_2', 'tooth_3', 'tooth_4', 'tooth_5', 'tooth_6', 'tooth_7', 'tooth_8',
        'tooth_9', 'tooth_10', 'tooth_11', 'tooth_12', 'tooth_13', 'tooth_14', 'tooth_15', 'tooth_16',
        'tooth_17', 'tooth_18', 'tooth_19', 'tooth_20', 'tooth_21', 'tooth_22', 'tooth_23', 'tooth_24',
        'tooth_25', 'tooth_26', 'tooth_27', 'tooth_28', 'tooth_29', 'tooth_30', 'tooth_31', 'tooth_32'
    )
    def _compute_selected_teeth(self):
        for record in self:
            selected = []
            for i in range(1, 33):  # Loop through teeth 1-32
                if record[f"tooth_{i}"]:  # Check if the tooth is selected
                    selected.append(f"Tooth -{i}")  # Append "Tooth -" before number
            record.selected_teeth = ", ".join(selected) if selected else "None"