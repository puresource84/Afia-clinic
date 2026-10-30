/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Odoo 18's built-in "last connected user" login switcher (public component
 * "web.user_switch") crashes on mount on this server build with:
 *   OwlError: Missing template: "web.login_user_switch"
 * Because the crash happens inside Owl's mount step (before the login
 * form's own "d-none" class gets removed by that same component's setup()),
 * the entire login form is left permanently hidden on every /web/login
 * page load — for every user, not just a specific role.
 *
 * This is a stock Odoo `web` module issue (confirmed: no Afia Clinic
 * customization touches this component, its template, or the
 * web.assets_frontend_lazy bundle), and the "remember last user, offer a
 * quick switcher" feature it provides is not something a single-clinic
 * login page needs anyway.
 *
 * Attempt 1: remove the component from the registry so it's never
 * constructed at all. Kept as a best-effort measure, but Odoo's own
 * public-root bootstrap snapshots/iterates "public_components" before
 * this file is guaranteed to have run relative to user_switch.js's own
 * registration, so this alone is not reliable.
 */
try {
    registry.category("public_components").remove("web.user_switch");
} catch {
    // ignore — registry entry may not exist yet depending on load order
}

/**
 * Attempt 2 (the reliable fix): regardless of whether the component above
 * crashes in the background, guarantee the actual visible symptom never
 * happens — force the login form visible ourselves. This runs independently
 * of Owl's mount/crash timing, so it isn't subject to the same race.
 */
function forceShowLoginForm() {
    const form = document.querySelector("form.oe_login_form");
    if (form && form.classList.contains("d-none")) {
        form.classList.remove("d-none");
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", forceShowLoginForm);
} else {
    forceShowLoginForm();
}
// Also watch for anything re-adding the class after our initial pass
// (e.g. the crashing component's setup() running just before it throws).
const loginFormObserver = new MutationObserver(forceShowLoginForm);
if (document.body) {
    loginFormObserver.observe(document.body, {
        attributes: true,
        attributeFilter: ["class"],
        subtree: true,
    });
}
