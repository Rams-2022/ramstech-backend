"""
WhatsApp sending — auto-detects provider from env vars.

Priority order:
  1. Clickatell    (recommended for SA — ZAR billing, local support)
  2. Twilio        (global, more expensive)
  3. Meta Cloud    (cheapest, most setup friction)
  4. Console       (fallback — logs to stdout, no send)

Env vars per provider:
  Clickatell:  CLICKATELL_API_KEY, CLICKATELL_WHATSAPP_CHANNEL_ID
  Twilio:      TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
  Meta Cloud:  META_WA_TOKEN, META_WA_PHONE_ID

All providers accept the same call:
  send_whatsapp(to="072 123 4567", body="Hello")

Returns dict: {"success": bool, "provider": str, "message_id": str|None,
               "error": str|None, "to": str}
"""
import os
import re
import json
import base64
import urllib.request
import urllib.parse
import urllib.error


# ═══════════════════════════════════════════════════════════════
# PHONE NORMALIZATION (SA-focused, but tolerant)
# ═══════════════════════════════════════════════════════════════
def normalize_phone(raw):
    """
    Normalize a phone number to E.164 (no +, digits only).
    Handles SA formats:
      072 123 4567     -> 27721234567
      +27 72 123 4567  -> 27721234567
      0027 72 123 4567 -> 27721234567
      27721234567      -> 27721234567
    """
    if not raw:
        return ""
    digits = re.sub(r"\D", "", str(raw))
    if not digits:
        return ""
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 10:
        # SA local: 0721234567 -> 27721234567
        digits = "27" + digits[1:]
    elif digits.startswith("27") and len(digits) == 11:
        pass  # already correct
    elif len(digits) == 9 and digits.startswith("7"):
        # missing leading 27
        digits = "27" + digits
    return digits


# ═══════════════════════════════════════════════════════════════
# PROVIDER DETECTION
# ═══════════════════════════════════════════════════════════════
def detect_provider():
    if os.getenv("CLICKATELL_API_KEY", "").strip() and \
       os.getenv("CLICKATELL_WHATSAPP_CHANNEL_ID", "").strip():
        return "clickatell"
    if os.getenv("TWILIO_ACCOUNT_SID", "").strip() and \
       os.getenv("TWILIO_AUTH_TOKEN", "").strip() and \
       os.getenv("TWILIO_WHATSAPP_FROM", "").strip():
        return "twilio"
    if os.getenv("META_WA_TOKEN", "").strip() and \
       os.getenv("META_WA_PHONE_ID", "").strip():
        return "meta"
    return "console"


def provider_status():
    """For /api/whatsapp/status — shows what's active without leaking secrets."""
    return {
        "provider": detect_provider(),
        "clickatell_configured": bool(os.getenv("CLICKATELL_API_KEY", "").strip()),
        "twilio_configured": bool(os.getenv("TWILIO_ACCOUNT_SID", "").strip()),
        "meta_configured": bool(os.getenv("META_WA_TOKEN", "").strip()),
    }


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════
def send_whatsapp(to, body, media_url=None):
    """
    Send a WhatsApp message. Auto-routes to configured provider.
    Never raises — always returns a result dict.
    """
    phone = normalize_phone(to)
    if not phone:
        return {"success": False, "provider": "none", "message_id": None,
                "error": "Invalid or empty phone number", "to": str(to or "")}

    provider = detect_provider()

    try:
        if provider == "clickatell":
            return _send_clickatell(phone, body, media_url)
        if provider == "twilio":
            return _send_twilio(phone, body, media_url)
        if provider == "meta":
            return _send_meta(phone, body, media_url)
        return _send_console(phone, body)
    except Exception as e:
        return {"success": False, "provider": provider, "message_id": None,
                "error": f"{type(e).__name__}: {e}", "to": phone}


# ═══════════════════════════════════════════════════════════════
# CONSOLE (fallback — logs, doesn't send)
# ═══════════════════════════════════════════════════════════════
def _send_console(phone, body):
    print(f"[whatsapp:console] → +{phone}\n{body}\n{'─'*40}")
    return {"success": True, "provider": "console", "message_id": None,
            "error": None, "to": phone}


# ═══════════════════════════════════════════════════════════════
# CLICKATELL
# Docs: https://docs.clickatell.com/channels/whatsapp/
# ═══════════════════════════════════════════════════════════════
def _send_clickatell(phone, body, media_url=None):
    api_key = os.getenv("CLICKATELL_API_KEY", "").strip()
    channel_id = os.getenv("CLICKATELL_WHATSAPP_CHANNEL_ID", "").strip()

    payload = {
        "channel": "whatsapp",
        "to": phone,
        "content": json.dumps({
            "type": "text",
            "text": {"body": body}
        }),
    }

    url = "https://platform.clickatell.com/v1/message"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg_id = None
            if isinstance(data, dict):
                msgs = data.get("messages") or []
                if msgs and isinstance(msgs, list):
                    msg_id = msgs[0].get("apiMessageId")
            return {"success": True, "provider": "clickatell",
                    "message_id": msg_id, "error": None, "to": phone}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")[:300]
        return {"success": False, "provider": "clickatell",
                "message_id": None, "error": f"HTTP {e.code}: {err_body}",
                "to": phone}


# ═══════════════════════════════════════════════════════════════
# TWILIO
# Docs: https://www.twilio.com/docs/whatsapp
# ═══════════════════════════════════════════════════════════════
def _send_twilio(phone, body, media_url=None):
    sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    sender = os.getenv("TWILIO_WHATSAPP_FROM", "").strip()  # "whatsapp:+14155238886"

    if not sender.startswith("whatsapp:"):
        sender = "whatsapp:" + sender

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    form = {
        "From": sender,
        "To": f"whatsapp:+{phone}",
        "Body": body,
    }
    if media_url:
        form["MediaUrl"] = media_url

    data = urllib.parse.urlencode(form).encode("utf-8")
    auth = base64.b64encode(f"{sid}:{token}".encode()).decode()

    req = urllib.request.Request(
        url, data=data,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode("utf-8"))
            return {"success": True, "provider": "twilio",
                    "message_id": d.get("sid"), "error": None, "to": phone}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")[:300]
        return {"success": False, "provider": "twilio",
                "message_id": None, "error": f"HTTP {e.code}: {err_body}",
                "to": phone}


# ═══════════════════════════════════════════════════════════════
# META CLOUD API
# Docs: https://developers.facebook.com/docs/whatsapp/cloud-api
# Note: outbound beyond 24h customer window requires approved templates.
# This sends a session (free-form) text — works when customer replied
# within last 24h. For template sends, you'll need extra plumbing.
# ═══════════════════════════════════════════════════════════════
def _send_meta(phone, body, media_url=None):
    token = os.getenv("META_WA_TOKEN", "").strip()
    phone_id = os.getenv("META_WA_PHONE_ID", "").strip()

    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": body, "preview_url": False},
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode("utf-8"))
            msg_id = None
            if isinstance(d, dict):
                msgs = d.get("messages") or []
                if msgs and isinstance(msgs, list):
                    msg_id = msgs[0].get("id")
            return {"success": True, "provider": "meta",
                    "message_id": msg_id, "error": None, "to": phone}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")[:300]
        return {"success": False, "provider": "meta",
                "message_id": None, "error": f"HTTP {e.code}: {err_body}",
                "to": phone}
