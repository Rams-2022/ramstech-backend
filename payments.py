"""
Payment gateway integration — auto-detects provider from env vars.

Priority order:
  1. Yoco       (recommended for SA — ZAR, local cards, instant settlement)
  2. PayFast    (SA alternative — more setup, older API)
  3. Stripe     (global — works in SA but settlement is slower)
  4. Console    (fallback — returns a fake URL for testing)

Env vars per provider:
  Yoco:      YOCO_SECRET_KEY  (sk_test_... or sk_live_...)
  PayFast:   PAYFAST_MERCHANT_ID, PAYFAST_MERCHANT_KEY, PAYFAST_PASSPHRASE
  Stripe:    STRIPE_SECRET_KEY

Webhook setup (in provider dashboard):
  Yoco:      https://yourdomain.com/api/payments/webhook/yoco
  PayFast:   https://yourdomain.com/api/payments/webhook/payfast
  Stripe:    https://yourdomain.com/api/payments/webhook/stripe
"""
import os
import re
import json
import hmac
import hashlib
import base64
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(tags=["payments"])


# ═══════════════════════════════════════════════════════════════
# PROVIDER DETECTION
# ═══════════════════════════════════════════════════════════════
def detect_provider():
    if os.getenv("YOCO_SECRET_KEY", "").strip():
        return "yoco"
    if os.getenv("PAYFAST_MERCHANT_ID", "").strip() and \
       os.getenv("PAYFAST_MERCHANT_KEY", "").strip():
        return "payfast"
    if os.getenv("STRIPE_SECRET_KEY", "").strip():
        return "stripe"
    return "console"


def provider_status():
    return {
        "provider": detect_provider(),
        "yoco_configured": bool(os.getenv("YOCO_SECRET_KEY", "").strip()),
        "payfast_configured": bool(os.getenv("PAYFAST_MERCHANT_ID", "").strip()),
        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY", "").strip()),
    }


def _public_base():
    """Base URL for redirects. Set PUBLIC_BASE_URL on Render."""
    base = os.getenv("PUBLIC_BASE_URL", "").strip()
    return base.rstrip("/") if base else "https://ramstech.onrender.com"


# ═══════════════════════════════════════════════════════════════
# CORE — create a payment link for an invoice
# ═══════════════════════════════════════════════════════════════
def create_payment_link(invoice):
    """
    Returns dict:
      {success, provider, url, ref, error, amount}
    Never raises.
    """
    try:
        amount_rands = float(invoice.get("total", 0)) - float(invoice.get("amount_paid", 0))
        if amount_rands <= 0.005:
            return {"success": False, "provider": "none", "url": None,
                    "ref": None, "error": "Nothing outstanding", "amount": 0}

        provider = detect_provider()
        cents = int(round(amount_rands * 100))
        inv_id = invoice.get("id", "")
        desc = f"Invoice {inv_id} — {invoice.get('description', '')[:40]}"

        if provider == "yoco":
            return _yoco_checkout(inv_id, cents, desc)
        if provider == "payfast":
            return _payfast_link(inv_id, amount_rands, desc)
        if provider == "stripe":
            return _stripe_link(inv_id, cents, desc)
        return _console_link(inv_id, amount_rands, desc)
    except Exception as e:
        return {"success": False, "provider": "error", "url": None,
                "ref": None, "error": f"{type(e).__name__}: {e}", "amount": 0}


# ═══════════════════════════════════════════════════════════════
# YOCO CHECKOUT
# Docs: https://developer.yoco.com/online/api-reference/checkout/
# ═══════════════════════════════════════════════════════════════
def _yoco_checkout(invoice_id, amount_cents, description):
    key = os.getenv("YOCO_SECRET_KEY", "").strip()
    base = _public_base()

    payload = {
        "amount": amount_cents,
        "currency": "ZAR",
        "successUrl": f"{base}/pay/success?inv={invoice_id}",
        "cancelUrl":  f"{base}/pay/cancelled?inv={invoice_id}",
        "failureUrl": f"{base}/pay/failed?inv={invoice_id}",
        "metadata": {
            "invoiceId": invoice_id,
            "source": "ramstech",
        },
    }

    req = urllib.request.Request(
        "https://online.yoco.com/v1/checkouts",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode("utf-8"))
            return {
                "success": True,
                "provider": "yoco",
                "url": d.get("redirectUrl"),
                "ref": d.get("id"),
                "error": None,
                "amount": amount_cents / 100,
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:300]
        return {"success": False, "provider": "yoco", "url": None,
                "ref": None, "error": f"HTTP {e.code}: {body}",
                "amount": amount_cents / 100}


# ═══════════════════════════════════════════════════════════════
# PAYFAST (custom integration — via standard payment form)
# Docs: https://developers.payfast.co.za/docs
# ═══════════════════════════════════════════════════════════════
def _payfast_link(invoice_id, amount_rands, description):
    merchant_id = os.getenv("PAYFAST_MERCHANT_ID", "").strip()
    merchant_key = os.getenv("PAYFAST_MERCHANT_KEY", "").strip()
    passphrase = os.getenv("PAYFAST_PASSPHRASE", "").strip()
    base = _public_base()
    sandbox = os.getenv("PAYFAST_SANDBOX", "").strip() == "1"

    form = {
        "merchant_id": merchant_id,
        "merchant_key": merchant_key,
        "return_url": f"{base}/pay/success?inv={invoice_id}",
        "cancel_url": f"{base}/pay/cancelled?inv={invoice_id}",
        "notify_url": f"{base}/api/payments/webhook/payfast",
        "m_payment_id": invoice_id,
        "amount": f"{amount_rands:.2f}",
        "item_name": f"Invoice {invoice_id}"[:100],
        "item_description": (description or "")[:255],
    }

    # build signature string in PayFast's exact order
    sig_str = urllib.parse.urlencode(form)
    if passphrase:
        sig_str += f"&passphrase={urllib.parse.quote_plus(passphrase)}"
    form["signature"] = hashlib.md5(sig_str.encode()).hexdigest()

    host = "sandbox.payfast.co.za" if sandbox else "www.payfast.co.za"
    url = f"https://{host}/eng/process?" + urllib.parse.urlencode(form)

    return {"success": True, "provider": "payfast", "url": url,
            "ref": invoice_id, "error": None, "amount": amount_rands}


# ═══════════════════════════════════════════════════════════════
# STRIPE CHECKOUT
# ═══════════════════════════════════════════════════════════════
def _stripe_link(invoice_id, amount_cents, description):
    key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    base = _public_base()

    form = {
        "mode": "payment",
        "success_url": f"{base}/pay/success?inv={invoice_id}",
        "cancel_url":  f"{base}/pay/cancelled?inv={invoice_id}",
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": "zar",
        "line_items[0][price_data][unit_amount]": str(amount_cents),
        "line_items[0][price_data][product_data][name]": f"Invoice {invoice_id}"[:100],
        "metadata[invoiceId]": invoice_id,
    }
    data = urllib.parse.urlencode(form).encode("utf-8")

    req = urllib.request.Request(
        "https://api.stripe.com/v1/checkout/sessions",
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode("utf-8"))
            return {"success": True, "provider": "stripe",
                    "url": d.get("url"), "ref": d.get("id"),
                    "error": None, "amount": amount_cents / 100}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:300]
        return {"success": False, "provider": "stripe", "url": None,
                "ref": None, "error": f"HTTP {e.code}: {body}",
                "amount": amount_cents / 100}


# ═══════════════════════════════════════════════════════════════
# CONSOLE FALLBACK
# ═══════════════════════════════════════════════════════════════
def _console_link(invoice_id, amount_rands, description):
    base = _public_base()
    url = f"{base}/pay/demo?inv={invoice_id}&amount={amount_rands:.2f}"
    print(f"[payments:console] link for {invoice_id}: R{amount_rands:.2f} → {url}")
    return {"success": True, "provider": "console", "url": url,
            "ref": f"console_{invoice_id}", "error": None,
            "amount": amount_rands}


# ═══════════════════════════════════════════════════════════════
# PUBLIC ENDPOINTS — /pay/*
# ═══════════════════════════════════════════════════════════════
@router.get("/pay/{invoice_id}", response_class=RedirectResponse)
def pay_redirect(invoice_id: str):
    """Customer taps this from WhatsApp — sends them straight to checkout."""
    from main import store_get
    inv = store_get("invoices", invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")

    # reuse an existing live link if we made one recently
    existing = inv.get("payment_link")
    if existing and existing.get("url") and not inv.get("paid"):
        return RedirectResponse(existing["url"], status_code=302)

    link = create_payment_link(inv)
    if not link.get("success"):
        raise HTTPException(500, f"Payment link failed: {link.get('error')}")

    inv["payment_link"] = {
        "url": link["url"],
        "provider": link["provider"],
        "ref": link["ref"],
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "amount": link["amount"],
    }
    from main import store_save
    store_save("invoices", invoice_id, inv)

    return RedirectResponse(link["url"], status_code=302)


def _success_page(title, message, color="#16a34a", icon="✓"):
    return HTMLResponse(f"""<!doctype html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
body{{font-family:-apple-system,"Segoe UI",Roboto,sans-serif;
margin:0;padding:40px 20px;background:#f5f5f5;text-align:center;color:#1a1a1a}}
.card{{max-width:400px;margin:60px auto;background:#fff;border-radius:16px;
padding:40px 28px;box-shadow:0 4px 20px rgba(0,0,0,0.06)}}
.icon{{font-size:56px;color:{color};margin-bottom:16px}}
h1{{margin:0 0 8px;font-size:22px;letter-spacing:-0.3px}}
p{{margin:0;color:#666;line-height:1.6;font-size:15px}}
.back{{display:inline-block;margin-top:24px;color:#111;font-weight:600;
text-decoration:none;border-bottom:2px solid #111;padding-bottom:2px}}
</style></head><body>
<div class="card">
  <div class="icon">{icon}</div>
  <h1>{title}</h1>
  <p>{message}</p>
</div></body></html>""")


@router.get("/pay/success")
def pay_success(inv: str = ""):
    return _success_page("Payment received",
                         f"Thank you! Invoice {inv} has been marked as paid. "
                         f"A receipt will follow on WhatsApp.")


@router.get("/pay/cancelled")
def pay_cancelled(inv: str = ""):
    return _success_page("Payment cancelled",
                         "No charge was made. You can pay any time — "
                         "just tap the link in your WhatsApp message again.",
                         color="#f59e0b", icon="!")


@router.get("/pay/failed")
def pay_failed(inv: str = ""):
    return _success_page("Payment failed",
                         "Something went wrong. Please try again, or contact "
                         "the workshop if the problem continues.",
                         color="#dc2626", icon="×")


@router.get("/pay/demo")
def pay_demo(inv: str = "", amount: str = "0"):
    return _success_page("Demo mode",
                         f"Console mode is active (no real gateway configured). "
                         f"Would have charged R{amount} for invoice {inv}.",
                         color="#666", icon="⚙")


# ═══════════════════════════════════════════════════════════════
# WEBHOOKS — provider notifies us payment succeeded
# ═══════════════════════════════════════════════════════════════
def _mark_paid(invoice_id, amount, provider, ref):
    from main import store_get, store_save
    inv = store_get("invoices", invoice_id)
    if not inv:
        return {"success": False, "error": "Invoice not found"}
    if inv.get("paid"):
        return {"success": True, "already": True}

    inv["amount_paid"] = float(inv.get("amount_paid", 0)) + float(amount)
    inv["paid"] = inv["amount_paid"] >= float(inv.get("total", 0)) - 0.005
    inv["payment_received"] = {
        "at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "provider": provider,
        "ref": ref,
        "amount": float(amount),
    }
    store_save("invoices", invoice_id, inv)
    print(f"[payments] invoice {invoice_id} marked paid via {provider} "
          f"(R{amount:.2f})")
    return {"success": True, "invoice_id": invoice_id, "paid": inv["paid"]}


@router.post("/api/payments/webhook/yoco")
async def webhook_yoco(request: Request):
    raw = await request.body()
    try:
        event = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    # Optional signature verification — set YOCO_WEBHOOK_SECRET to enable
    secret = os.getenv("YOCO_WEBHOOK_SECRET", "").strip()
    if secret:
        sig_header = request.headers.get("webhook-signature", "")
        # Yoco format: "v1,<base64>" — verify HMAC-SHA256 over the raw body
        try:
            received = sig_header.split(",", 1)[1] if "," in sig_header else sig_header
            expected = base64.b64encode(
                hmac.new(secret.encode(), raw, hashlib.sha256).digest()
            ).decode()
            if not hmac.compare_digest(received, expected):
                print("[payments] yoco webhook signature mismatch")
                raise HTTPException(401, "Bad signature")
        except HTTPException:
            raise
        except Exception as e:
            print(f"[payments] yoco signature check error: {e}")

    # Yoco sends: {type: "payment.succeeded", payload: {metadata: {invoiceId}, amount, id}}
    event_type = event.get("type") or event.get("eventType") or ""
    if "succeeded" not in event_type.lower():
        return {"success": True, "ignored": event_type}

    payload = event.get("payload") or event.get("data") or {}
    metadata = payload.get("metadata") or {}
    invoice_id = metadata.get("invoiceId") or payload.get("invoiceId")
    amount_cents = payload.get("amount") or 0
    ref = payload.get("id") or ""

    if not invoice_id:
        return {"success": False, "error": "no invoiceId in webhook"}

    return _mark_paid(invoice_id, amount_cents / 100, "yoco", ref)


@router.post("/api/payments/webhook/payfast")
async def webhook_payfast(request: Request):
    """PayFast sends form-encoded data. We verify signature then mark paid."""
    form = dict(await request.form())
    if not form:
        raise HTTPException(400, "Empty payload")

    # PayFast signature check
    passphrase = os.getenv("PAYFAST_PASSPHRASE", "").strip()
    received_sig = form.pop("signature", "")
    sig_str = urllib.parse.urlencode(form)
    if passphrase:
        sig_str += f"&passphrase={urllib.parse.quote_plus(passphrase)}"
    expected = hashlib.md5(sig_str.encode()).hexdigest()

    if received_sig and received_sig != expected:
        print("[payments] payfast signature mismatch")
        raise HTTPException(401, "Bad signature")

    # PayFast status: COMPLETE, FAILED, PENDING, CANCELLED
    status = (form.get("payment_status") or "").upper()
    invoice_id = form.get("m_payment_id") or ""
    amount = float(form.get("amount_gross") or 0)

    if status != "COMPLETE":
        return {"success": True, "ignored": status}

    return _mark_paid(invoice_id, amount, "payfast", form.get("pf_payment_id", ""))


@router.post("/api/payments/webhook/stripe")
async def webhook_stripe(request: Request):
    raw = await request.body()
    try:
        event = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if secret:
        sig_header = request.headers.get("stripe-signature", "")
        try:
            # Stripe format: t=...,v1=...
            parts = dict(p.split("=", 1) for p in sig_header.split(","))
            ts = parts.get("t", "")
            v1 = parts.get("v1", "")
            signed = f"{ts}.".encode() + raw
            expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(v1, expected):
                raise HTTPException(401, "Bad signature")
        except HTTPException:
            raise
        except Exception as e:
            print(f"[payments] stripe signature check error: {e}")

    if event.get("type") != "checkout.session.completed":
        return {"success": True, "ignored": event.get("type")}

    session = event.get("data", {}).get("object", {})
    invoice_id = session.get("metadata", {}).get("invoiceId")
    amount_total = session.get("amount_total", 0)

    if not invoice_id:
        return {"success": False, "error": "no invoiceId in session"}

    return _mark_paid(invoice_id, amount_total / 100, "stripe", session.get("id", ""))


# ═══════════════════════════════════════════════════════════════
# API — expose link creation + status
# ═══════════════════════════════════════════════════════════════
@router.get("/api/payments/status")
def payments_status():
    return provider_status()


@router.post("/api/payments/link/{invoice_id}")
def create_link(invoice_id: str):
    from main import store_get, store_save
    inv = store_get("invoices", invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")

    link = create_payment_link(inv)
    if not link.get("success"):
        return link

    inv["payment_link"] = {
        "url": link["url"],
        "provider": link["provider"],
        "ref": link["ref"],
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "amount": link["amount"],
    }
    store_save("invoices", invoice_id, inv)
    return link
