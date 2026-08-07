import base64
import hashlib
import hmac
import logging
from datetime import date, datetime, timedelta

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared secret used to sign/verify renewal codes.
#
# IMPORTANT: this constant must match the one in the private, ITCS-only code
# generator script (ITCS Projects/itcs_internal_tools/generate_license_code.py
# or gui_generate_license_code.py — never shipped to any clinic). If this key
# is ever suspected to have leaked, rotate it here AND in the generator, and
# treat all previously-issued codes as untrustworthy going forward (existing
# clinics keep running on their last-applied expiry date; you'd just reissue
# their next renewal code with the new key).
#
# This is deliberately a static compiled-in secret, not a per-clinic key —
# same trade-off as any traditional offline software license key scheme.
# It protects against casual tampering, not a determined attacker with full
# access to ITCS's own systems. See the chat discussion 2026-07-17 for why
# that's the right level of effort here.
#
# 2026-07-30: moved OUT of this file and into secret_config.py (gitignored,
# NEVER committed to this public repo) so the actual secret value is never
# visible to anyone who clones this repo. Copy secret_config.py.example to
# secret_config.py and fill in the real value locally on your own server —
# this repo intentionally ships without a working secret_config.py.
# ---------------------------------------------------------------------------
try:
    from ..secret_config import LICENSE_SECRET as _LICENSE_SECRET
except ImportError:
    _LICENSE_SECRET = None


def _require_secret():
    if _LICENSE_SECRET is None:
        raise UserError(
            "ITCS License Manager is not configured: secret_config.py is "
            "missing from this module's folder on the server. Copy "
            "secret_config.py.example to secret_config.py and fill in the "
            "real secret (contact ITCS if you don't have it) before "
            "applying or generating renewal codes."
        )
    return _LICENSE_SECRET


def _sign(clinic_code, expiry_str):
    msg = f"{clinic_code}|{expiry_str}".encode()
    return hmac.new(_require_secret(), msg, hashlib.sha256).digest()[:6]


def decode_renewal_code(code):
    """Decode + verify a renewal code. Returns (clinic_code, expiry_date) or
    raises ValueError with a human-readable reason."""
    raw = code.strip().upper()
    if raw.startswith("AFIA-"):
        raw = raw[5:]
    raw = raw.replace("-", "")
    padded = raw + ("=" * ((8 - len(raw) % 8) % 8))
    try:
        decoded = base64.b32decode(padded)
    except Exception:
        raise ValueError("Malformed code (not valid AFIA license format).")

    if len(decoded) < 7:
        raise ValueError("Malformed code (too short).")

    payload, sig = decoded[:-6], decoded[-6:]
    try:
        clinic_code, expiry_str = payload.decode().split("|")
    except Exception:
        raise ValueError("Malformed code (bad payload).")

    expected_sig = _sign(clinic_code, expiry_str)
    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("Invalid code — signature does not match. This code was not issued by ITCS, or has been altered.")

    try:
        expiry = datetime.strptime(expiry_str, "%Y%m%d").date()
    except Exception:
        raise ValueError("Malformed code (bad date).")

    return clinic_code, expiry


class ItcsLicense(models.Model):
    _name = "itcs.license"
    _description = "ITCS License (internal — clinic staff must never see this model)"
    _rec_name = "clinic_code"

    # Deliberately no chatter/mail mixin here — this model should never
    # surface in the clinic's own activity/notification feeds.
    clinic_name = fields.Char(
        help="Human-readable clinic name, for your own reference only "
             "(e.g. 'Amal Medical Clinic 1'). Not encoded in renewal codes "
             "— only clinic_code is.",
    )
    clinic_code = fields.Char(
        required=True,
        help="Unique identifier for this clinic instance, agreed with ITCS "
             "at onboarding (e.g. AFIA-ALNOOR). Must match the clinic_code "
             "encoded in any renewal code applied here.",
    )
    expiry_date = fields.Date(
        required=True,
        help="Current license/AMC expiry date. Set automatically when a "
             "valid renewal code is applied — do not edit by hand.",
    )
    grace_days = fields.Integer(
        default=7,
        help="Days after expiry_date before the instance switches to "
             "read-only mode. Never a full lockout — see module description.",
    )
    telegram_bot_token = fields.Char(
        help="Bot token for the ITCS alert bot (separate from any patient-"
             "facing reminder bot). Alerts go to telegram_chat_id below.",
    )
    telegram_chat_id = fields.Char(
        help="Your (ITCS) personal or group Telegram chat ID that should "
             "receive expiry alerts for this clinic.",
    )
    last_alert_sent = fields.Date(readonly=True)

    state = fields.Selection(
        [("active", "Active"), ("grace", "Grace period"), ("read_only", "Read-only")],
        compute="_compute_state",
        store=False,
    )
    days_to_expiry = fields.Integer(compute="_compute_state", store=False)

    renewal_ids = fields.One2many("itcs.license.renewal", "license_id", readonly=True)

    def action_open_apply_code_wizard(self):
        """Opens the 'Apply Renewal Code' popup. Deliberately a wizard
        (transient model) rather than a non-stored field + button on this
        form: type="object" buttons trigger an implicit save of the record
        first, which silently discards any non-stored field's just-typed
        value before the button's own method ever runs. A wizard avoids
        that save-then-call ordering problem entirely."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Apply Renewal Code",
            "res_model": "itcs.license.apply.code.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_license_id": self.id},
        }

    @api.depends("expiry_date", "grace_days")
    def _compute_state(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.expiry_date:
                rec.state = "read_only"
                rec.days_to_expiry = 0
                continue
            delta = (rec.expiry_date - today).days
            rec.days_to_expiry = delta
            if delta >= 0:
                rec.state = "active"
            elif delta >= -rec.grace_days:
                rec.state = "grace"
            else:
                rec.state = "read_only"

    def action_apply_renewal_code(self, code):
        """Validate a renewal code and, if valid, extend this license."""
        self.ensure_one()
        try:
            clinic_code, new_expiry = decode_renewal_code(code)
        except ValueError as e:
            raise UserError(str(e))

        if clinic_code != self.clinic_code:
            raise UserError(
                "This code was issued for a different clinic instance "
                "(%s), not this one (%s). Double check with ITCS."
                % (clinic_code, self.clinic_code)
            )

        if new_expiry <= (self.expiry_date or date.min):
            raise UserError(
                "This code's expiry date (%s) is not later than the "
                "current one (%s) — it may have already been applied, or "
                "an older code was pasted by mistake."
                % (new_expiry, self.expiry_date)
            )

        self.env["itcs.license.renewal"].create({
            "license_id": self.id,
            "code": code.strip().upper(),
            "applied_on": fields.Date.context_today(self),
            "previous_expiry": self.expiry_date,
            "new_expiry": new_expiry,
        })
        self.expiry_date = new_expiry
        self._refresh_read_only_flag()
        return True

    def _refresh_read_only_flag(self):
        """Cheap flag read by write_guard.py on every write, so we don't
        need a full license lookup on every ORM write. Recomputed here and
        by the daily cron."""
        self.ensure_one()
        param = self.env["ir.config_parameter"].sudo()
        param.set_param("itcs_license.read_only", "1" if self.state == "read_only" else "0")

    def _send_telegram_alert(self, text):
        self.ensure_one()
        if not (self.telegram_bot_token and self.telegram_chat_id):
            _logger.warning("ITCS license alert not sent (no bot token/chat id configured): %s", text)
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage",
                json={"chat_id": self.telegram_chat_id, "text": text},
                timeout=10,
            )
        except Exception:
            _logger.exception("Failed to send ITCS license Telegram alert")

    def cron_check_licenses(self):
        """Daily scheduled action: refresh read-only flag, alert ITCS at
        the configured thresholds."""
        today = fields.Date.context_today(self)
        thresholds = (14, 7, 3, 0)
        for rec in self.search([]):
            rec._refresh_read_only_flag()

            if rec.days_to_expiry in thresholds:
                if rec.last_alert_sent != today:
                    rec._send_telegram_alert(
                        f"⏳ {rec.clinic_code}: license expires in "
                        f"{rec.days_to_expiry} day(s) ({rec.expiry_date})."
                    )
                    rec.last_alert_sent = today
            elif rec.state == "grace" and rec.days_to_expiry % 2 == 0:
                # still inside grace period, past the last named threshold —
                # ping every 2 days so it doesn't go silent
                if rec.last_alert_sent != today:
                    rec._send_telegram_alert(
                        f"⚠️ {rec.clinic_code}: license expired "
                        f"{-rec.days_to_expiry} day(s) ago, in grace period "
                        f"({rec.grace_days} day grace). ({rec.expiry_date})"
                    )
                    rec.last_alert_sent = today
            elif rec.state == "read_only" and rec.days_to_expiry % 7 == 0:
                if rec.last_alert_sent != today:
                    rec._send_telegram_alert(
                        f"🔴 {rec.clinic_code}: license expired "
                        f"{-rec.days_to_expiry} day(s) ago — instance is now "
                        f"READ-ONLY. Renewal code needed. ({rec.expiry_date})"
                    )
                    rec.last_alert_sent = today


class ItcsLicenseRenewal(models.Model):
    _name = "itcs.license.renewal"
    _description = "ITCS License Renewal Log (internal)"
    _order = "applied_on desc"

    license_id = fields.Many2one("itcs.license", required=True, ondelete="cascade")
    code = fields.Char(required=True)
    applied_on = fields.Date(required=True)
    previous_expiry = fields.Date()
    new_expiry = fields.Date()
