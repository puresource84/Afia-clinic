/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { onMounted, onWillStart } from "@odoo/owl";

// Shows the ITCS license seat-availability banner (used/available seats for
// the clinic's plan) above the Patients and Dentists list views.
//
// Why this exists / how it's wired: earlier attempt tried a made-up
// `banner_route` XML attribute directly on <list>, which isn't a real Odoo
// view attribute and fails RelaxNG validation for every module load, not
// just this one (see project_afia_click_everywhere_qa_2026-08-15 memory).
// The valid way to pass view-specific config without inventing arch
// attributes is the action's `context` — see views/patient_license_banner_views.xml
// and views/hr_employee_license_banner_views.xml for the `itcs_banner_kind`
// context key. This patch is a no-op on every list view that doesn't set
// that key, so it can't affect anything outside the two lists it targets.
const ROUTES = {
    patient: "/itcs_license/patients_banner",
    dentist: "/itcs_license/staff_banner",
};

patch(ListController.prototype, {
    setup() {
        super.setup();
        const kind = this.props.context && this.props.context.itcs_banner_kind;
        this.itcsBannerRoute = ROUTES[kind];
        this.itcsBannerHtml = "";
        if (this.itcsBannerRoute) {
            onWillStart(async () => {
                try {
                    const res = await fetch(this.itcsBannerRoute);
                    this.itcsBannerHtml = res.ok ? await res.text() : "";
                } catch {
                    this.itcsBannerHtml = "";
                }
            });
            onMounted(() => {
                if (!this.itcsBannerHtml || !this.rootRef.el) {
                    return;
                }
                const content = this.rootRef.el.querySelector(".o_content") || this.rootRef.el;
                if (content.querySelector(".o_itcs_license_banner")) {
                    return; // already inserted (e.g. re-mount)
                }
                const wrapper = document.createElement("div");
                wrapper.className = "o_itcs_license_banner";
                wrapper.innerHTML = this.itcsBannerHtml;
                content.prepend(wrapper);
            });
        }
    },
});
