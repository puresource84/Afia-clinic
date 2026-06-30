/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";

const CONDITION_COLORS = {
    healthy: "#c8e6c9",
    caries: "#ef5350",
    filled: "#42a5f5",
    crown: "#ab47bc",
    root_canal: "#ffa726",
    implant: "#26a69a",
    bridge: "#8d6e63",
    veneer: "#f48fb1",
    mobile: "#ffee58",
    fractured: "#ff7043",
    extracted: "#bdbdbd",
    missing: "#757575",
};

// FDI layouts. Adult: upper right→left then left; lower mirrors.
const UPPER = ["18", "17", "16", "15", "14", "13", "12", "11",
               "21", "22", "23", "24", "25", "26", "27", "28"];
const LOWER = ["48", "47", "46", "45", "44", "43", "42", "41",
               "31", "32", "33", "34", "35", "36", "37", "38"];
// Deciduous (pediatric) dentition, FDI 51-85.
const UPPER_DECID = ["55", "54", "53", "52", "51",
                     "61", "62", "63", "64", "65"];
const LOWER_DECID = ["85", "84", "83", "82", "81",
                     "71", "72", "73", "74", "75"];

export class OdontogramField extends Component {
    static template = "dental_charting_pro.Odontogram";
    static props = { ...standardFieldProps };

    setup() {
        this.action = useService("action");
        this.ui = useState({ pediatric: false });
    }

    get upper() {
        return this.ui.pediatric ? UPPER_DECID : UPPER;
    }
    get lower() {
        return this.ui.pediatric ? LOWER_DECID : LOWER;
    }
    get toothWidth() {
        return this.ui.pediatric ? 64 : 44;
    }
    get svgWidth() {
        return this.upper.length * this.toothWidth + 8;
    }

    togglePediatric() {
        this.ui.pediatric = !this.ui.pediatric;
    }

    get chartData() {
        return this.props.record.data[this.props.name] || {};
    }

    // Normalize legacy (string) and v2 ({condition, surfaces}) payloads.
    toothInfo(fdi) {
        const raw = this.chartData[fdi];
        if (!raw) {
            return { condition: null, surfaces: [] };
        }
        if (typeof raw === "string") {
            return { condition: raw, surfaces: [] };
        }
        return { condition: raw.condition || null, surfaces: raw.surfaces || [] };
    }

    toothTitle(fdi) {
        const { condition, surfaces } = this.toothInfo(fdi);
        if (!condition) {
            return `Tooth ${fdi}`;
        }
        const surf = surfaces.length ? ` [${surfaces.join("")}]` : "";
        return `Tooth ${fdi}: ${condition}${surf}`;
    }

    /**
     * Per-surface regions for one tooth cell (A3, widget v2).
     * Anatomy mapping:
     *  - Mesial faces the midline: right side of the cell for quadrants
     *    1/4/5/8 (drawn left of the midline), left side for 2/3/6/7.
     *  - Buccal is the outer side: top for upper arch, bottom for lower arch.
     *  - Occlusal is the center square.
     * Coloring: surfaces listed on the record get the condition color;
     * whole-tooth conditions (no surfaces) color all five regions.
     */
    toothRegions(fdi, x, y, w, h, arch) {
        const { condition, surfaces } = this.toothInfo(fdi);
        const condColor = CONDITION_COLORS[condition] || "#fafafa";
        const base = "#fafafa";
        const wholeTooth = condition && surfaces.length === 0;
        const fill = (code) =>
            wholeTooth || surfaces.includes(code) ? condColor : base;

        const quadrant = fdi[0];
        const mesialRight = ["1", "4", "5", "8"].includes(quadrant);
        const buccalTop = arch === "upper";

        // Outer rect corners and inner (occlusal) square corners.
        const ix = x + w * 0.27, iy = y + h * 0.27;
        const iw = w * 0.46, ih = h * 0.46;
        const pts = (arr) => arr.map((p) => p.join(",")).join(" ");
        const trap = {
            top: pts([[x, y], [x + w, y], [ix + iw, iy], [ix, iy]]),
            bottom: pts([[x, y + h], [x + w, y + h], [ix + iw, iy + ih], [ix, iy + ih]]),
            left: pts([[x, y], [ix, iy], [ix, iy + ih], [x, y + h]]),
            right: pts([[x + w, y], [ix + iw, iy], [ix + iw, iy + ih], [x + w, y + h]]),
        };
        return [
            { key: "B", points: trap[buccalTop ? "top" : "bottom"], fill: fill("B") },
            { key: "L", points: trap[buccalTop ? "bottom" : "top"], fill: fill("L") },
            { key: "M", points: trap[mesialRight ? "right" : "left"], fill: fill("M") },
            { key: "D", points: trap[mesialRight ? "left" : "right"], fill: fill("D") },
            {
                key: "O",
                points: pts([[ix, iy], [ix + iw, iy], [ix + iw, iy + ih], [ix, iy + ih]]),
                fill: fill("O"),
            },
        ];
    }

    async openTooth(fdi) {
        if (!this.props.record.resId) {
            return;
        }
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: `Tooth ${fdi}`,
            res_model: "dental.tooth.record",
            views: [[false, "list"], [false, "form"]],
            domain: [
                ["patient_id", "=", this.props.record.resId],
                ["tooth_fdi", "=", fdi],
            ],
            context: {
                default_patient_id: this.props.record.resId,
                default_tooth_fdi: fdi,
            },
            target: "current",
        });
    }
}

export const odontogramField = {
    component: OdontogramField,
    supportedTypes: ["json"],
};

registry.category("fields").add("odontogram", odontogramField);
