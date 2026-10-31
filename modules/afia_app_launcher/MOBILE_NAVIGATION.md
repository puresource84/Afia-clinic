# Afia App Launcher — Navbar Interception & Mobile Navigation

This note documents how `navbar_patch.js` interacts with Odoo 18's navbar, why it was
changed on 2026-08-20, and the constraints any future edit to this file must respect.
It exists because the previous version of this patch silently broke in-app navigation
on mobile for ~5 weeks before being caught during a mobile click-everywhere QA pass —
the goal is to make sure that specific mistake is never repeated.

## What the patch is for

Afia Clinic replaces Odoo's default "Apps" home screen with a branded launcher
(`afia_app_launcher`, the tile grid with search). `navbar_patch.js` is what makes the
apps-grid icon in the top navbar open that branded launcher instead of Odoo's default
apps dropdown.

## The bug (fixed 2026-08-20)

Odoo's navbar renders **two different icons** depending on viewport, not one:

| Viewport | Selector | Odoo's native behavior |
|---|---|---|
| Desktop (`!env.isSmall`) | `.o_navbar_apps_menu` | Opens a small dropdown listing all installed apps ("switch app"). The *current app's own section menu* (Appointments / Patients / Billing & Insurance / Reporting / Configuration for Afia Clinic) is rendered separately, inline, in the top navbar — always visible. |
| Mobile (`env.isSmall`) | `.o_menu_toggle` (the ☰ hamburger) | Opens `web.NavBar.AppsMenu.Sidebar` — a slide-out panel that does **double duty**: by default it shows the **current app's own section menu** (`currentAppSections`, the same items desktop shows inline), and it has its own "All Apps" button inside that same sidebar to switch apps. |

The original patch intercepted clicks on **both** selectors and unconditionally redirected
them to the Afia Launcher:

```js
// OLD — do not reintroduce this
const mobileBtn = e.target.closest(".o_menu_toggle");
if (!appsBtn && !mobileBtn) return;
...
action.doAction({ type: "ir.actions.client", tag: "afia_app_launcher" });
```

On desktop this was harmless — the section menu is rendered separately and was never
touched. On mobile it was not harmless: the hamburger is the **only** entry point to
the section menu (Configuration, Billing & Insurance, Reporting, etc.) once you're
inside a specific view. Redirecting it to the launcher meant that on a phone, once you
opened e.g. Patients, there was **no way to reach Configuration** short of manually
going back to the launcher and hoping a tile existed for it. This went unnoticed for a
long time because desktop testing never exercises `.o_menu_toggle` at all — it only
exists in the DOM when `env.isSmall`.

**Confirmed by reading Odoo core**, not guessed:
`odoo/addons/web/static/src/webclient/navbar/navbar.xml`, templates
`web.NavBar.AppsMenu` (~line 78, shows `.o_menu_toggle` only when `env.isSmall`) and
`web.NavBar.AppsMenu.Sidebar` (~line 104, renders `currentAppSections` via
`web.SectionMenu` by default, with `state.isAllAppsMenuOpened` toggling to the apps
list — that toggle is the sidebar's own "All Apps" button, `onAllAppsBtnClick`).

## The fix

Only intercept `.o_navbar_apps_menu` (desktop). Do **not** intercept `.o_menu_toggle`.
Odoo's native mobile sidebar already does the right thing by default — it needs to be
left alone, not redirected.

```js
const appsBtn = e.target.closest(
    ".o_navbar_apps_menu button, .o_navbar_apps_menu [role='button']"
);
if (!appsBtn) return;
...
```

Net effect: desktop still redirects the apps-grid icon to the Afia Launcher (unchanged
behavior). Mobile hamburger now opens Odoo's native section-menu sidebar, which already
has its own "All Apps" button for switching apps — so branded-launcher access is still
one tap away on mobile, it just lives inside the sidebar's native switcher instead of
being forced as the hamburger's only behavior.

## Rule for future changes to this file

**Never add `.o_menu_toggle` (or any other mobile-only navbar trigger) back into the
interception list without first checking, in Odoo core, whether that element's native
behavior does something on mobile that has no equivalent elsewhere in the UI.** The
desktop apps-grid icon is safe to intercept because the section menu is rendered
elsewhere (inline in the navbar) and losing the dropdown loses nothing else. Mobile
triggers are frequently **overloaded** (one control doing two jobs) — confirm via the
actual XML/JS template, not by assumption, before intercepting.

If a future requirement genuinely needs the Afia Launcher reachable from inside the
mobile sidebar too, the correct approach is to add an *additional* entry/button inside
`web.NavBar.AppsMenu.Sidebar`'s app-list view (the `state.isAllAppsMenuOpened` branch) —
which per `feedback_no_core_odoo_edits.md` means overriding/patching that specific OWL
component from this module, not intercepting the trigger that opens it. Do not edit
Odoo core files under `odoo/addons/web/` to achieve this.

## Related fix in this module: app launcher mobile scroll (also 2026-08-16/20)

Unrelated bug, same QA pass: `static/src/app_launcher/app_launcher.scss`'s
`.afia-launcher` rule used `min-height: calc(100vh - 46px)`, assuming the outer page
scrolls. It doesn't — Odoo's `.o_action_manager` hands every action a fixed-height slot
(`overflow-y: hidden`) and expects the action's own root to provide its own scroll
region. Fixed by making `.afia-launcher` itself `height: 100%; overflow-y: auto;`. This
rarely overflowed on desktop (room for ~12-15 tiles) but broke almost immediately on a
mobile-height viewport with no way to reach tiles past the fold.

## Deploy notes for this module specifically

- Pure JS/SCSS content edits (this fix) only need a version bump in `__manifest__.py`
  + `ir.module.module.button_immediate_upgrade` via RPC. No service restart required.
- If a change ever ADDS a new file to the manifest's `data` list, a full Odoo service
  restart is required before any upgrade will pick it up — `update_list()` alone is not
  sufficient for already-installed modules. See `dental_ux_fixes`'s "Add Staff User"
  wizard menu fix (2026-08-20) for a confirmed example of this.
- Mirror any change here to the two other copies of this module:
  `Afia Clinic - Unified Package/afia_app_launcher/` and
  `afia-clinic-repo/modules/afia_app_launcher/`.
