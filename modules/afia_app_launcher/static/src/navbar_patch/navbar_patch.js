/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Afia Navbar Interceptor
 * ────────────────────────
 * In Odoo 18 Community the apps-grid button (oi-apps icon) is rendered by the
 * <Dropdown> component inside .o_navbar_apps_menu — there is NO
 * toggleHomeMenu() on NavBar.prototype to patch.
 *
 * We register a capture-phase click listener that fires BEFORE the Dropdown
 * sees the event.  It prevents the default popup from opening and navigates
 * to the Afia App Launcher instead.
 *
 * Selectors covered:
 *   Desktop — any button inside .o_navbar_apps_menu
 *   Mobile  — .o_menu_toggle (the hamburger <a> link)
 */
const afiaNavbarInterceptorService = {
    dependencies: ["action"],
    start(_env, { action }) {
        document.addEventListener(
            "click",
            (e) => {
                const appsBtn   = e.target.closest(
                    ".o_navbar_apps_menu button, .o_navbar_apps_menu [role='button']"
                );
                const mobileBtn = e.target.closest(".o_menu_toggle");

                if (!appsBtn && !mobileBtn) return;

                // Stop Odoo's Dropdown from opening
                e.stopPropagation();
                e.preventDefault();

                action.doAction({
                    type: "ir.actions.client",
                    tag: "afia_app_launcher",
                });
            },
            true // capture phase — fires before OWL/Dropdown handlers
        );
    },
};

registry.category("services").add("afia_navbar_interceptor", afiaNavbarInterceptorService);
