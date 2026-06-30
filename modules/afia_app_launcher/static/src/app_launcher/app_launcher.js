/** @odoo-module **/

import {
    Component,
    useState,
    useRef,
    onMounted,
    onWillUnmount,
} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";

/**
 * Detect image MIME type from the first characters of a base64 string.
 * Covers PNG, JPEG, GIF, WebP, SVG, BMP — falls back to image/png.
 */
function _detectImageMime(b64) {
    if (b64.startsWith('iVBOR')) return 'image/png';
    if (b64.startsWith('/9j/'))  return 'image/jpeg';
    if (b64.startsWith('R0lG'))  return 'image/gif';
    if (b64.startsWith('UklG'))  return 'image/webp';
    if (b64.startsWith('PHN2'))  return 'image/svg+xml';
    if (b64.startsWith('Qk0'))   return 'image/bmp';
    return 'image/png';
}

/**
 * Afia App Launcher
 * -----------------
 * Home page for Odoo 18 Community:
 *   • App tiles always visible (role-filtered by Odoo ACL)
 *   • Global search hidden until user types — shows a dropdown of matching
 *     apps AND submenus (Windows-style combobox), keyboard-navigable
 *   • Drag-and-drop reordering persisted in localStorage per user
 *   • Labels follow the Odoo session language
 */
export class AfiaAppLauncher extends Component {
    static template = "afia_app_launcher.AppLauncher";
    // Odoo's ControllerComponent passes these standard props to every client
    // action component. Declaring them (all optional) silences OWL's prop
    // validation warnings in debug mode.
    static props = {
        action:            { optional: true },
        actionId:          { optional: true },
        updateActionState: { optional: true },
        className:         { optional: true },
        "*":               true,   // forward-compatible catch-all
    };

    // ------------------------------------------------------------------ setup

    setup() {
        this.menuService   = useService("menu");
        this.actionService = useService("action");
        this.searchRef     = useRef("search");
        this.rootRef       = useRef("root");

        /** Flat index of every accessible menu item, built once on mount. */
        this._menuIndex = [];

        this.state = useState({
            apps:          [],   // root apps for the tile grid (never filtered)
            query:         "",
            searchVisible: false,
            results:       [],   // dropdown items
            activeIdx:     -1,   // keyboard-nav cursor in results
            dragSrc:       null,
            dragOver:      null,
        });

        this._anyKeyHandler = (e) => this._onAnyKey(e);

        onMounted(() => {
            this._loadApps();
            this._buildMenuIndex();
            this._loadBranding();
            document.addEventListener("keydown", this._anyKeyHandler);
        });

        onWillUnmount(() => {
            document.removeEventListener("keydown", this._anyKeyHandler);
        });
    }

    // ---------------------------------------------------------- app discovery

    _storageKey() {
        const uid = (odoo.session_info && odoo.session_info.uid) || 0;
        return `afia_launcher_order_uid_${uid}`;
    }

    _loadApps() {
        const raw   = this.menuService.getApps ? this.menuService.getApps() : [];
        const order = this._loadOrder();

        let apps;
        if (order.length) {
            const indexed = new Map(order.map((id, i) => [id, i]));
            apps = [...raw].sort((a, b) => {
                const ai = indexed.has(a.id) ? indexed.get(a.id) : 9999;
                const bi = indexed.has(b.id) ? indexed.get(b.id) : 9999;
                return ai - bi;
            });
        } else {
            apps = [...raw];
        }

        this.state.apps = apps;
    }

    _loadOrder() {
        try {
            const raw = localStorage.getItem(this._storageKey());
            return raw ? JSON.parse(raw) : [];
        } catch { return []; }
    }

    _saveOrder() {
        try {
            localStorage.setItem(
                this._storageKey(),
                JSON.stringify(this.state.apps.map((a) => a.id))
            );
        } catch { /* storage full */ }
    }

    // ------------------------------------------------------- full menu index

    /**
     * Traverse the entire menu tree accessible to this user and build a flat
     * list used for the search dropdown.
     * Each entry: { id, name, path, app }
     *   path  — breadcrumb string: "Afia Clinic › Patients › Treatment Plans"
     *   app   — the root app menu object (used for colour / initials)
     */
    _buildMenuIndex() {
        const index = [];

        const traverse = (menu, breadcrumb, rootApp) => {
            const app  = rootApp || menu;
            const path = breadcrumb ? breadcrumb + " › " + menu.name : menu.name;

            index.push({ id: menu.id, name: menu.name, path, app });

            const children = (menu.children || [])
                .map((id) => this.menuService.getMenu(id))
                .filter(Boolean);

            for (const child of children) {
                traverse(child, path, app);
            }
        };

        const apps = this.menuService.getApps ? this.menuService.getApps() : [];
        for (const app of apps) {
            traverse(app, "", null);
        }

        this._menuIndex = index;
    }

    // ------------------------------------------------------ branding / theming

    /**
     * Fetch white-label config from the server and apply as CSS custom
     * properties on the root element so the SCSS `::before` pseudo-element
     * can render the background image at the configured opacity.
     * Fails silently — no background is shown if the call errors or if no
     * image has been uploaded in Settings.
     */
    async _loadBranding() {
        try {
            const data = await rpc("/afia_launcher/branding", {});
            const el   = this.rootRef.el;
            if (!el || !data || !data.bg_image) return;

            // Detect image MIME type from the leading base64 bytes
            const mime = _detectImageMime(data.bg_image);
            el.style.setProperty(
                "--afia-bg-image",
                `url('data:${mime};base64,${data.bg_image}')`
            );
            el.style.setProperty(
                "--afia-bg-opacity",
                String(data.bg_opacity || 0.6)
            );
        } catch {
            // branding config unavailable — silent no-op
        }
    }

    // --------------------------------------------------------------- open app

    onContainerClick(e) {
        if (e.target === e.currentTarget) this._clearSearch();
    }

    onTileClick(e) {
        const id  = parseInt(e.currentTarget.dataset.appId, 10);
        const app = this.state.apps.find((a) => a.id === id);
        if (!app) return;
        this._openMenu(app);
    }

    _openMenu(menuOrId) {
        const menu = typeof menuOrId === "object"
            ? menuOrId
            : this.menuService.getMenu(menuOrId);
        if (!menu) return;
        if (this.menuService.selectMenu) {
            this.menuService.selectMenu(menu);
        } else if (menu.actionID) {
            this.actionService.doAction(menu.actionID, { clearBreadcrumbs: true });
        }
    }

    // ------------------------------------------------------- search & dropdown

    /** Keydown anywhere on the page while the launcher is shown. */
    _onAnyKey(e) {
        // Already in an input? Let it be.
        const tag = document.activeElement && document.activeElement.tagName;
        if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
        if (e.ctrlKey || e.altKey || e.metaKey) return;
        if (!e.key || e.key.length !== 1) return;

        this.state.searchVisible = true;
        this._runSearch(e.key);

        const el = this.searchRef.el;
        if (el) { el.value = e.key; el.focus(); }
        e.preventDefault();
    }

    onSearchInput(e) {
        const val = e.target.value;
        this.state.query = val;
        if (!val) {
            this._clearSearch();
        } else {
            this._runSearch(val);
        }
    }

    onSearchKeydown(e) {
        const len = this.state.results.length;
        if (e.key === "Escape") {
            this._clearSearch();
        } else if (e.key === "ArrowDown") {
            e.preventDefault();
            this.state.activeIdx = Math.min(this.state.activeIdx + 1, len - 1);
            this._scrollActiveIntoView();
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            this.state.activeIdx = Math.max(this.state.activeIdx - 1, 0);
            this._scrollActiveIntoView();
        } else if (e.key === "Enter") {
            const r = this.state.results[this.state.activeIdx];
            if (r) { this._selectResult(r); }
        }
    }

    _runSearch(term) {
        this.state.query = term;
        const lower = term.toLowerCase();

        const seen    = new Set();
        const results = [];

        for (const item of this._menuIndex) {
            if (seen.has(item.id)) continue;
            if (
                item.name.toLowerCase().includes(lower) ||
                item.path.toLowerCase().includes(lower)
            ) {
                seen.add(item.id);
                results.push(item);
                if (results.length >= 15) break; // cap at 15 rows
            }
        }

        this.state.results  = results;
        this.state.activeIdx = results.length ? 0 : -1;
    }

    _selectResult(result) {
        this._openMenu(result.id);
        this._clearSearch();
    }

    _clearSearch() {
        this.state.query         = "";
        this.state.searchVisible = false;
        this.state.results       = [];
        this.state.activeIdx     = -1;
        const el = this.searchRef.el;
        if (el) { el.value = ""; el.blur(); }
    }

    /** Click on a dropdown result row. */
    onResultClick(e) {
        const id     = parseInt(e.currentTarget.dataset.menuId, 10);
        const result = this.state.results.find((r) => r.id === id);
        if (result) this._selectResult(result);
    }

    /** Mouse hover highlights the row. */
    onResultHover(e) {
        const id  = parseInt(e.currentTarget.dataset.menuId, 10);
        const idx = this.state.results.findIndex((r) => r.id === id);
        if (idx !== -1) this.state.activeIdx = idx;
    }

    _scrollActiveIntoView() {
        // Allow the DOM to update before scrolling
        Promise.resolve().then(() => {
            const el = document.querySelector(".afia-launcher__result--active");
            if (el) el.scrollIntoView({ block: "nearest" });
        });
    }

    // --------------------------------------------------------- drag-and-drop

    onDragStart(e) {
        const id = parseInt(e.currentTarget.dataset.appId, 10);
        this.state.dragSrc = id;
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", String(id));
    }

    onDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        const id = parseInt(e.currentTarget.dataset.appId, 10);
        if (this.state.dragOver !== id) this.state.dragOver = id;
    }

    onDragLeave() {
        this.state.dragOver = null;
    }

    onDrop(e) {
        e.preventDefault();
        const srcId    = this.state.dragSrc;
        const targetId = parseInt(e.currentTarget.dataset.appId, 10);

        if (!srcId || srcId === targetId) { this._resetDrag(); return; }

        const apps   = [...this.state.apps];
        const srcIdx = apps.findIndex((a) => a.id === srcId);
        const tgtIdx = apps.findIndex((a) => a.id === targetId);

        if (srcIdx !== -1 && tgtIdx !== -1) {
            const [moved] = apps.splice(srcIdx, 1);
            apps.splice(tgtIdx, 0, moved);
            this.state.apps = apps;
            this._saveOrder();
        }
        this._resetDrag();
    }

    onDragEnd() { this._resetDrag(); }

    _resetDrag() {
        this.state.dragSrc  = null;
        this.state.dragOver = null;
    }

    // ---------------------------------------------------------------- helpers

    getIconSrc(app)    { return app.webIconData || null; }

    getTileColor(app) {
        const colours = [
            "#6366f1","#0ea5e9","#10b981","#f59e0b",
            "#ef4444","#8b5cf6","#ec4899","#14b8a6",
            "#f97316","#84cc16","#06b6d4","#a78bfa",
        ];
        let hash = 0;
        for (const ch of (app.name || "")) {
            hash = ((hash << 5) - hash) + ch.charCodeAt(0);
            hash |= 0;
        }
        return colours[Math.abs(hash) % colours.length];
    }

    getInitials(app) {
        const words = (app.name || "?").trim().split(/\s+/);
        return words.length === 1
            ? words[0][0].toUpperCase()
            : (words[0][0] + words[1][0]).toUpperCase();
    }
}

registry.category("actions").add("afia_app_launcher", AfiaAppLauncher);
