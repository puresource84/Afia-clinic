/** @odoo-module **/

/**
 * float_time_dropdown — a field widget for Float fields that:
 *   • Displays the value as HH:MM (like float_time)
 *   • Opens a dropdown of all 15-minute slots when focused
 *   • Filters the list as the user types
 *   • Allows completely manual entry (e.g. 09:07, 11:03)
 *   • Commits on blur or slot selection; reverts on Escape / invalid input
 */

import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Float (e.g. 9.5) → "HH:MM" string (e.g. "09:30"). */
function toHHMM(v) {
    if (v === false || v === undefined || v === null) return "";
    const h = Math.floor(v);
    const m = Math.round((v - h) * 60);
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

/** "HH:MM" or "H:MM" string → float. Returns NaN on invalid input. */
function parseHHMM(str) {
    const match = String(str || "").trim().match(/^(\d{1,2}):(\d{2})$/);
    if (!match) return NaN;
    const h = parseInt(match[1], 10);
    const m = parseInt(match[2], 10);
    if (h > 23 || m > 59) return NaN;
    return h + m / 60;
}

/** All 96 fifteen-minute slots from 00:00 to 23:45. */
const ALL_SLOTS = (() => {
    const out = [];
    for (let h = 0; h < 24; h++) {
        for (let m = 0; m < 60; m += 15) {
            out.push({
                label: `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`,
                value: h + m / 60,
            });
        }
    }
    return out;
})();

/**
 * Smart filter:
 *   "9"  → 09:xx  (single digit → try zero-padded first)
 *   "09" → 09:xx
 *   "14" → 14:xx
 *   "09:3" → 09:30, 09:45
 */
function filterSlots(raw) {
    if (!raw) return ALL_SLOTS;
    // Direct prefix match ("09", "14:", "09:3")
    const direct = ALL_SLOTS.filter((s) => s.label.startsWith(raw));
    if (direct.length) return direct;
    // Single digit → try zero-padded ("9" → "09")
    if (/^\d$/.test(raw)) {
        const padded = ALL_SLOTS.filter((s) => s.label.startsWith("0" + raw));
        if (padded.length) return padded;
    }
    // Fallback: contains anywhere
    return ALL_SLOTS.filter((s) => s.label.includes(raw));
}

// ── Component ─────────────────────────────────────────────────────────────────

export class FloatTimeDropdown extends Component {
    static template = "dental_patient_flow.FloatTimeDropdown";
    static props = {
        ...standardFieldProps,
        placeholder: { type: String, optional: true },
    };

    setup() {
        this.inputRef = useRef("input");

        this.state = useState({
            text: toHHMM(this.props.record.data[this.props.name] || 0),
            open: false,
            slots: ALL_SLOTS,
            // Dropdown position (fixed, so it escapes any overflow:hidden parent)
            top: 0,
            left: 0,
            minWidth: 0,
        });

        // Close when clicking outside the widget
        this._onDocMousedown = (ev) => {
            if (!ev.target.closest?.(".o_float_time_dd")) {
                this.state.open = false;
            }
        };
        // Close on any scroll (so the dropdown doesn't float away)
        this._onScroll = () => {
            this.state.open = false;
        };

        onMounted(() => {
            document.addEventListener("mousedown", this._onDocMousedown);
            window.addEventListener("scroll", this._onScroll, true);
        });
        onWillUnmount(() => {
            document.removeEventListener("mousedown", this._onDocMousedown);
            window.removeEventListener("scroll", this._onScroll, true);
        });
    }

    get currentFloat() {
        return this.props.record.data[this.props.name] || 0;
    }

    /** Place the dropdown just below the input using fixed positioning. */
    _reposition() {
        const rect = this.inputRef.el?.getBoundingClientRect();
        if (rect) {
            this.state.top = rect.bottom;
            this.state.left = rect.left;
            this.state.minWidth = rect.width;
        }
    }

    // ── Event handlers ────────────────────────────────────────────────────────

    onFocus() {
        // Show full list and current formatted value when field gets focus
        this.state.text = toHHMM(this.currentFloat);
        this.state.slots = ALL_SLOTS;
        this._reposition();
        this.state.open = true;
    }

    onInput(ev) {
        const raw = ev.target.value;
        this.state.text = raw;
        this.state.slots = filterSlots(raw);
        this._reposition();
        this.state.open = true;
    }

    onKeydown(ev) {
        if (ev.key === "Escape") {
            // Revert to last saved value and close
            this.state.text = toHHMM(this.currentFloat);
            this.state.open = false;
        } else if (ev.key === "Tab" || ev.key === "Enter") {
            // Commit on Tab / Enter
            this._commit();
            this.state.open = false;
        }
    }

    onBlur() {
        // Delay slightly so mousedown on a dropdown slot fires first (preventing
        // the slot click from being swallowed by blur).
        setTimeout(() => {
            this._commit();
            this.state.open = false;
        }, 160);
    }

    /** Called when the user clicks a slot from the dropdown list. */
    pickSlot(slot) {
        this.props.record.update({ [this.props.name]: slot.value });
        this.state.text = slot.label;
        this.state.open = false;
    }

    // ── Internal ──────────────────────────────────────────────────────────────

    _commit() {
        const val = parseHHMM(this.state.text);
        if (!isNaN(val)) {
            this.props.record.update({ [this.props.name]: val });
            this.state.text = toHHMM(val);
        } else {
            // Invalid text → restore last valid value
            this.state.text = toHHMM(this.currentFloat);
        }
    }
}

registry.category("fields").add("float_time_dropdown", {
    component: FloatTimeDropdown,
    supportedTypes: ["float"],
});
