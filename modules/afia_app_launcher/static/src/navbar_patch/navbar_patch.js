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
 *
 * 2026-08-20: .o_menu_toggle (the mobile hamburger) is intentionally NOT
 * intercepted anymore. On mobile (env.isSmall) that hamburger opens Odoo's
 * native web.NavBar.AppsMenu.Sidebar, which does double duty: by default it
 * shows the CURRENT APP's own section menu (Appointments/Patients/Billing &
 * Insurance/Reporting/Configuration for Afia Clinic), and it has its own
 * built-in "All Apps" button to switch apps from inside that same sidebar.
 * Redirecting it unconditionally to the Afia Launcher (as this file used to)
 * silently destroyed the ONLY way to reach in-app sections on a phone —
 * confirmed via odoo/addons/web/static/src/webclient/navbar/navbar.xml,
 * template web.NavBar.AppsMenu.Sidebar (currentAppSections rendered via
 * web.SectionMenu when state.isAllAppsMenuOpened is false). Desktop is
 * unaffected: .o_navbar_apps_menu (the separate oi-apps icon) still redirects
 * to the Afia Launcher, and desktop already renders currentAppSections
 * inline in the top navbar, so nothing is lost there.
 */
const afiaNavbarInterceptorService = {
    dependencies: ["action"],
    start(_env, { action }) {
        document.addEventListener(
            "click",
            (e) => {
                const appsBtn = e.target.closest(
                    ".o_navbar_apps_menu button, .o_navbar_apps_menu [role='button']"
                );

                if (!appsBtn) return;

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
