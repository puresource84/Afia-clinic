/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";

const CONDITION_COLORS = {
    healthy: "#ffffff",
    caries: "#ef5350",
    filled: "#42a5f5",
    crown: "#ffb300",
    root_canal: "#ff8a00",
    implant: "#26a69a",
    bridge: "#8d6e63",
    veneer: "#ec407a",
    mobile: "#fdd835",
    fractured: "#ff7043",
    extracted: "#7e57c2",
    missing: "#7e57c2",
};

const CONDITIONS = [
    ["healthy", "Healthy"], ["caries", "Caries"], ["filled", "Filled"], ["crown", "Crown"],
    ["root_canal", "Root canal"], ["implant", "Implant"], ["bridge", "Bridge"],
    ["veneer", "Veneer"], ["mobile", "Mobility"], ["fractured", "Fractured"],
    ["extracted", "Extracted"], ["missing", "Missing"],
];

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

// Anatomically-shaped occlusal-view outlines, one per tooth family, in a
// shared 0-36 local coordinate space. Used both as the visible outline
// stroke and as the clip path each tooth's four surface triangles are
// masked against, so a molar reads as a molar and an incisor reads as a
// flat blade rather than every tooth being the same generic circle.
const OUTLINE_PATHS = {
    molar: "M9,4 C13,2 23,2 27,4 C33,7 34,13 34,18 C34,23 33,29 27,32 " +
           "C23,34 13,34 9,32 C3,29 2,23 2,18 C2,13 3,7 9,4 Z",
    premolar: "M14,3 C16,2 20,2 22,3 C26,5 27,10 27,18 C27,26 26,31 22,33 " +
              "C20,34 16,34 14,33 C10,31 9,26 9,18 C9,10 10,5 14,3 Z",
    canine: "M18,2 C21,2 23,5 24,9 C26,14 27,20 27,24 C27,30 23,34 18,34 " +
            "C13,34 9,30 9,24 C9,20 10,14 12,9 C13,5 15,2 18,2 Z",
    incisor: "M6,16 C6,12 10,9 18,9 C26,9 30,12 30,16 C30,17.5 30,18.5 30,20 " +
             "C30,24 26,27 18,27 C10,27 6,24 6,20 C6,18.5 6,17.5 6,16 Z",
};

// Region keys used in the focus panel / staging, in the order the surface
// checkboxes/regions are laid out (top/right/bottom/left/center). B/L flip
// with arch (buccal is the outer surface), M/D flip with quadrant (mesial
// always faces the midline).
const REGION_KEYS = ["top", "right", "bottom", "left", "center"];

export class OdontogramField extends Component {
    static template = "dental_charting.Odontogram";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.ui = useState({
            pediatric: false,
            active: null,       // FDI of the tooth currently focused/enlarged
            pending: {},        // { fdi: { top, right, bottom, left, center } } staged surfaces
            condition: "caries",
            note: "",
            saving: false,
        });
    }

    get conditions() {
        return CONDITIONS.map(([code, label]) => ({ code, label }));
    }

    conditionColor(code) {
        return CONDITION_COLORS[code] || "#ffffff";
    }

    get upper() {
        return this.ui.pediatric ? UPPER_DECID : UPPER;
    }
    get lower() {
        return this.ui.pediatric ? LOWER_DECID : LOWER;
    }

    togglePediatric() {
        this.ui.pediatric = !this.ui.pediatric;
        this.ui.active = null;
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
        const staged = this.ui.pending[fdi];
        const parts = [];
        if (condition) {
            parts.push(`${condition}${surfaces.length ? ` [${surfaces.join("")}]` : ""}`);
        }
        if (staged) {
            parts.push("(staged, unsaved)");
        }
        return parts.length ? `Tooth ${fdi}: ${parts.join(" ")}` : `Tooth ${fdi}`;
    }

    // Legend chips shown under the ring: every non-healthy condition the
    // model supports, paired with its color, so the chart stays readable
    // without needing a separate key elsewhere in the UI.
    get legendEntries() {
        return CONDITIONS.filter(([code]) => code !== "healthy")
            .map(([code, label]) => ({ code, label, color: CONDITION_COLORS[code] }));
    }

    conditionLabel(condition) {
        if (!condition) {
            return "Healthy";
        }
        return condition.replace("_", " ").replace(/^./, (c) => c.toUpperCase());
    }

    // 1st digit of an FDI code = quadrant, 2nd digit = position in the
    // quadrant. Positions 1-2 are incisors, 3 is the canine; permanent
    // quadrants (1-4) have premolars at 4-5 and molars at 6-8, deciduous
    // quadrants (5-8) skip premolars entirely (positions 4-5 are molars).
    toothType(fdi) {
        const quadrant = fdi[0];
        const position = fdi[1];
        const deciduous = ["5", "6", "7", "8"].includes(quadrant);
        if (["1", "2"].includes(position)) {
            return "incisor";
        }
        if (position === "3") {
            return "canine";
        }
        if (deciduous) {
            return "molar";
        }
        return ["4", "5"].includes(position) ? "premolar" : "molar";
    }

    outlinePath(type) {
        return OUTLINE_PATHS[type] || OUTLINE_PATHS.molar;
    }

    archOf(fdi) {
        return this.upper.includes(fdi) ? "upper" : "lower";
    }

    /**
     * Whole-mouth ring layout: teeth are placed around an oval arch
     * (upper teeth along the top half, lower teeth along the bottom
     * half) instead of two straight rows, matching how a dentist and
     * patient naturally read a full-mouth chart.
     */
    get ringTeeth() {
        const cx = 150, cy = 170, rx = 110, ry = 140;
        const place = (arr, arch) => arr.map((fdi, i) => {
            const step = 150 / Math.max(arr.length - 1, 1);
            const angle = arch === "upper" ? 195 + step * i : 165 - step * i;
            const rad = (angle * Math.PI) / 180;
            return {
                fdi,
                arch,
                type: this.toothType(fdi),
                x: cx + rx * Math.cos(rad),
                y: cy + ry * Math.sin(rad),
            };
        });
        return [...place(this.upper, "upper"), ...place(this.lower, "lower")];
    }

    // Maps a tooth's saved (or staged) surface codes to top/right/bottom/
    // left/center regions, oriented per-arch/per-quadrant as described
    // above `REGION_KEYS`.
    regionKeys(fdi, arch) {
        const quadrant = fdi[0];
        const mesialRight = ["1", "4", "5", "8"].includes(quadrant);
        const buccalTop = arch === "upper";
        return {
            top: buccalTop ? "B" : "L",
            bottom: buccalTop ? "L" : "B",
            right: mesialRight ? "M" : "D",
            left: mesialRight ? "D" : "M",
            center: "O",
        };
    }

    /**
     * Per-surface fill colors for one tooth's ring glyph: staged (unsaved)
     * surfaces take priority and render in the in-progress condition
     * color; otherwise the tooth's saved condition/surfaces render as
     * before. Whole-tooth conditions (no surfaces recorded) color every
     * region.
     */
    toothRegions(fdi, arch) {
        const keys = this.regionKeys(fdi, arch);
        const staged = this.ui.pending[fdi];
        const { condition, surfaces } = this.toothInfo(fdi);
        const savedColor = CONDITION_COLORS[condition] || "#ffffff";
        const stagedColor = this.conditionColor(this.ui.condition);
        const wholeSavedTooth = condition && surfaces.length === 0;

        const fill = (code) => {
            if (staged && staged[code]) {
                return stagedColor;
            }
            if (wholeSavedTooth || surfaces.includes(code)) {
                return savedColor;
            }
            return "#ffffff";
        };
        return {
            top: fill(keys.top),
            right: fill(keys.right),
            bottom: fill(keys.bottom),
            left: fill(keys.left),
            center: fill(keys.center),
        };
    }

    isStaged(fdi) {
        return Boolean(this.ui.pending[fdi]);
    }

    // ── Focus / staging interaction ─────────────────────────────────────

    selectActive(fdi) {
        this.ui.active = this.ui.active === fdi ? null : fdi;
    }

    get activeType() {
        return this.ui.active ? this.toothType(this.ui.active) : null;
    }
    get activeArch() {
        return this.ui.active ? this.archOf(this.ui.active) : null;
    }
    get activeRegions() {
        return this.ui.active ? this.toothRegions(this.ui.active, this.activeArch) : null;
    }
    get activeInfo() {
        return this.ui.active ? this.toothInfo(this.ui.active) : null;
    }
    get activeStagedKeys() {
        if (!this.ui.active) {
            return [];
        }
        const staged = this.ui.pending[this.ui.active];
        return staged ? REGION_KEYS.filter((k) => staged[k]) : [];
    }

    // Toggle one region of the currently-focused tooth in/out of the
    // pending stage. Staging any surface on a tooth adds it to
    // `ui.pending`; clearing the last surface removes the tooth entirely.
    toggleSurface(regionKey) {
        if (!this.ui.active) {
            return;
        }
        const fdi = this.ui.active;
        const current = { ...(this.ui.pending[fdi] || {}) };
        current[regionKey] = !current[regionKey];
        if (Object.values(current).some(Boolean)) {
            this.ui.pending = { ...this.ui.pending, [fdi]: current };
        } else {
            const next = { ...this.ui.pending };
            delete next[fdi];
            this.ui.pending = next;
        }
    }

    get pendingFdis() {
        return Object.keys(this.ui.pending);
    }
    get pendingCount() {
        return this.pendingFdis.length;
    }

    clearSelection() {
        this.ui.pending = {};
        this.ui.note = "";
    }

    // Batch-save: one Save click writes one dental.tooth.record per staged
    // tooth, all sharing the chosen condition + note. Then reload the
    // record so the computed odontogram_data and the embedded
    // tooth_record_ids list both reflect the new rows immediately.
    async saveBatch() {
        if (!this.pendingCount || !this.props.record.resId) {
            return;
        }
        this.ui.saving = true;
        try {
            const keys = REGION_KEYS;
            // When this page was opened from an appointment's Dental Chart
            // smart button, the action context carries these defaults so
            // new records auto-link back to that appointment/doctor
            // (and treatment, if the appointment has exactly one) instead
            // of being left blank. Opening from the global Patients menu
            // has none of these in context, so they're simply omitted.
            const ctx = this.props.record.context || {};
            const linkVals = {};
            if (ctx.default_appointment_id) {
                linkVals.appointment_id = ctx.default_appointment_id;
            }
            if (ctx.default_doctor_id) {
                linkVals.doctor_id = ctx.default_doctor_id;
            }
            if (ctx.default_treatment_id) {
                linkVals.treatment_id = ctx.default_treatment_id;
            }
            const vals_list = this.pendingFdis.map((fdi) => {
                const arch = this.archOf(fdi);
                const regionKeys = this.regionKeys(fdi, arch);
                const staged = this.ui.pending[fdi];
                const surfaceOf = (code) => keys.some((k) => regionKeys[k] === code && staged[k]);
                return {
                    patient_id: this.props.record.resId,
                    tooth_fdi: fdi,
                    condition: this.ui.condition,
                    notes: this.ui.note || false,
                    surface_mesial: surfaceOf("M"),
                    surface_occlusal: surfaceOf("O"),
                    surface_distal: surfaceOf("D"),
                    surface_buccal: surfaceOf("B"),
                    surface_lingual: surfaceOf("L"),
                    ...linkVals,
                };
            });
            await this.orm.create("dental.tooth.record", vals_list);
            this.clearSelection();
            this.ui.active = null;
            await this.props.record.load();
        } finally {
            this.ui.saving = false;
        }
    }
}

export const odontogramField = {
    component: OdontogramField,
    supportedTypes: ["json"],
};

registry.category("fields").add("odontogram", odontogramField);
