"""
Auto-reminder scheduler.
Runs a daily pass that chases overdue debtors automatically.

Two ways to trigger:
  1. Externally: POST /api/auto-remind/run  (from cron-job.org, GitHub Actions, etc.)
  2. Internally: asyncio loop started at app startup (checks hourly)

Settings stored in workshop record under "auto_remind":
  enabled         bool    default True
  min_days        int     default 30   — only chase invoices >= this many days overdue
  cooldown_days   int     default 7    — don't re-remind within this many days
  max_per_day     int     default 50   — safety limit
  hour_utc        int     default 7    — preferred hour (UTC) for auto-run
  channel         str     default "whatsapp"
"""
from fastapi import APIRouter, Request
from datetime import datetime, timedelta
import asyncio

router = APIRouter(tags=["auto-remind"])

DEFAULT_SETTINGS = {
    "enabled": True,
    "min_days": 30,
    "cooldown_days": 7,
    "max_per_day": 50,
    "hour_utc": 7,
    "channel": "whatsapp",
    "last_run": None,
    "last_run_sent": 0,
    "last_run_skipped": 0,
    "last_run_reason": None,
}


def _get_settings():
    from main import get_workshop_data
    w = get_workshop_data() or {}
    s = w.get("auto_remind") or {}
    merged = dict(DEFAULT_SETTINGS)
    merged.update(s)
    return merged


def _save_settings(s):
    from main import get_workshop_data, save_workshop_data
    w = dict(get_workshop_data() or {})
    w["auto_remind"] = s
    save_workshop_data(w)
    return s


def _parse(s):
    if not s:
        return None
    for fmt, cut in (("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(s[:cut], fmt)
        except ValueError:
            continue
    return None


def _build_reminder(name, total, days, tone):
    if tone == "urgent":
        return (f"Hi {name}, your account balance of R{total:,.2f} is now "
                f"{days} days overdue. Please arrange payment or contact us "
                f"to discuss a payment plan.")
    if tone == "firm":
        return (f"Hi {name}, your outstanding balance is R{total:,.2f} "
                f"({days} days). Please settle at your earliest convenience, "
                f"or reply to arrange a plan.")
    return (f"Hi {name}, friendly reminder: R{total:,.2f} outstanding on your "
            f"account. No rush — settle when convenient. Thank you!")


def _run_pass(dry_run=False, force=False):
    """Execute one auto-reminder pass. Returns summary dict."""
    from main import store_list, store_save
    from aged_debtors import aged_debtors
    from whatsapp import send_whatsapp

    settings = _get_settings()
    if not settings["enabled"] and not force:
        return {"success": False, "reason": "auto_remind disabled",
                "sent": 0, "skipped": 0, "checked": 0}

    try:
        report = aged_debtors()
    except Exception as e:
        return {"success": False, "error": f"debtors report failed: {e}",
                "sent": 0, "skipped": 0, "checked": 0}

    min_days = int(settings["min_days"])
    cooldown = int(settings["cooldown_days"])
    max_today = int(settings["max_per_day"])
    cooldown_cutoff = datetime.now() - timedelta(days=cooldown)

    sent = 0
    skipped = 0
    details = []

    for cust in report["customers"]:
        if sent >= max_today:
            skipped += 1
            continue
        if cust["oldest_days"] < min_days:
            skipped += 1
            continue

        # cooldown check
        lr = _parse(cust.get("last_reminder"))
        if lr and lr > cooldown_cutoff:
            skipped += 1
            details.append({"customer": cust["customer"], "action": "skip",
                            "reason": f"reminded {cust['last_reminder']}"})
            continue

        tone = "urgent" if cust["oldest_days"] >= 90 else \
               "firm" if cust["oldest_days"] >= 60 else "friendly"
        msg = _build_reminder(cust["customer"], cust["total"],
                              cust["oldest_days"], tone)

        phone = cust.get("phone", "")
        if not phone:
            skipped += 1
            details.append({"customer": cust["customer"], "action": "skip",
                            "reason": "no phone number"})
            continue

        if dry_run:
            sent += 1
            details.append({"customer": cust["customer"], "action": "would_send",
                            "total": cust["total"], "days": cust["oldest_days"]})
            continue

        result = send_whatsapp(phone, msg)

        # log the reminder on every unpaid invoice
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        invoices = [i for i in store_list("invoices")
                    if (i.get("customer") or "").strip() == cust["customer"]
                    and (float(i.get("total", 0)) - float(i.get("amount_paid", 0))) > 0.005]
        for inv in invoices:
            rem = inv.get("reminders", [])
            rem.append({
                "sent": stamp,
                "channel": settings["channel"],
                "tone": tone,
                "provider": result.get("provider", ""),
                "message_id": result.get("message_id"),
                "success": result.get("success", False),
                "error": result.get("error"),
                "source": "auto",
            })
            inv["reminders"] = rem
            store_save("invoices", inv["id"], inv)

        if result.get("success"):
            sent += 1
            details.append({"customer": cust["customer"], "action": "sent",
                            "total": cust["total"], "days": cust["oldest_days"],
                            "provider": result.get("provider")})
        else:
            skipped += 1
            details.append({"customer": cust["customer"], "action": "failed",
                            "error": result.get("error")})

    if not dry_run:
        settings["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        settings["last_run_sent"] = sent
        settings["last_run_skipped"] = skipped
        settings["last_run_reason"] = "manual" if force else "auto"
        _save_settings(settings)

    return {
        "success": True,
        "dry_run": dry_run,
        "checked": len(report["customers"]),
        "sent": sent,
        "skipped": skipped,
        "details": details,
        "as_of": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ── Endpoints ────────────────────────────────────────────────────
@router.post("/api/auto-remind/run")
async def run_now(request: Request):
    """
    Trigger one pass.
      ?dry=1   — simulate only, don't send
      ?force=1 — run even if disabled
    """
    q = request.query_params
    dry = q.get("dry") in ("1", "true", "yes")
    force = q.get("force") in ("1", "true", "yes")
    try:
        return _run_pass(dry_run=dry, force=force)
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {e}"}


@router.get("/api/auto-remind/status")
def auto_remind_status():
    s = _get_settings()
    return {
        "settings": s,
        "server_time_utc": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "server_time_local": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


@router.post("/api/auto-remind/settings")
async def update_settings(r: Request):
    d = await r.json()
    s = _get_settings()
    for k in ("enabled", "min_days", "cooldown_days", "max_per_day",
              "hour_utc", "channel"):
        if k in d:
            s[k] = d[k]
    _save_settings(s)
    return {"success": True, "settings": s}


# ── In-process scheduler (best-effort, works when app stays awake) ──
_scheduler_task = None


async def _scheduler_loop():
    """Check every 30 min; fire once per day at settings['hour_utc']."""
    await asyncio.sleep(90)  # brief startup delay
    last_fired_date = None
    while True:
        try:
            now_utc = datetime.utcnow()
            s = _get_settings()
            hour = int(s.get("hour_utc", 7))
            today = now_utc.strftime("%Y-%m-%d")
            if (s.get("enabled") and now_utc.hour >= hour
                    and last_fired_date != today):
                print(f"[auto-remind] firing scheduled pass for {today}")
                try:
                    result = _run_pass()
                    print(f"[auto-remind] sent={result.get('sent')} "
                          f"skipped={result.get('skipped')}")
                except Exception as e:
                    print(f"[auto-remind] run error: {e}")
                last_fired_date = today
        except Exception as e:
            print(f"[auto-remind] loop error: {e}")
        await asyncio.sleep(1800)  # 30 min


def start_scheduler():
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        try:
            loop = asyncio.get_event_loop()
            _scheduler_task = loop.create_task(_scheduler_loop())
            print("[auto-remind] scheduler started")
        except Exception as e:
            print(f"[auto-remind] could not start scheduler: {e}")


# ── UI toggle (injected into debtors modal) ──────────────────────
AUTO_REMIND_HTML = """
<script>
(function(){
  function injectToggle(){
    const actions = document.querySelector('.rt-db-actions');
    if (!actions || document.getElementById('rt-ar-toggle')) return false;
    const btn = document.createElement('button');
    btn.id = 'rt-ar-toggle';
    btn.textContent = '⚙ Auto-remind';
    btn.style.marginLeft = 'auto';
    btn.onclick = async () => {
      const r = await fetch('/api/auto-remind/status');
      const d = await r.json();
      const s = d.settings;
      const info = [
        `Auto-remind: ${s.enabled ? 'ON' : 'OFF'}`,
        `Chase when: ${s.min_days}+ days overdue`,
        `Cooldown: every ${s.cooldown_days} days`,
        `Max/day: ${s.max_per_day}`,
        `Last run: ${s.last_run || 'never'}`,
        `Last sent: ${s.last_run_sent} · skipped ${s.last_run_skipped}`,
        '',
        'Commands:',
        '  on / off          — toggle',
        '  days 30           — change min_days',
        '  cooldown 7        — change cooldown',
        '  run               — run now',
        '  dry               — dry run (no sends)',
        '',
        'Type a command and press OK.'
      ].join('\\n');
      const input = prompt(info);
      if (!input) return;
      const cmd = input.trim().toLowerCase();
      try {
        if (cmd === 'on' || cmd === 'off') {
          await fetch('/api/auto-remind/settings', {method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({enabled: cmd === 'on'})});
        } else if (cmd.startsWith('days')) {
          const n = parseInt(cmd.split(/\\s+/)[1], 10);
          if (n > 0) await fetch('/api/auto-remind/settings', {method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({min_days: n})});
        } else if (cmd.startsWith('cooldown')) {
          const n = parseInt(cmd.split(/\\s+/)[1], 10);
          if (n > 0) await fetch('/api/auto-remind/settings', {method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({cooldown_days: n})});
        } else if (cmd === 'run') {
          const r2 = await fetch('/api/auto-remind/run', {method:'POST'});
          const d2 = await r2.json();
          alert(`Sent: ${d2.sent}\\nSkipped: ${d2.skipped}\\nChecked: ${d2.checked}`);
        } else if (cmd === 'dry') {
          const r2 = await fetch('/api/auto-remind/run?dry=1', {method:'POST'});
          const d2 = await r2.json();
          alert(`DRY RUN\\nWould send: ${d2.sent}\\nSkipped: ${d2.skipped}`);
        }
      } catch(e) { alert('Error: ' + e.message); }
      btn.click();  // refresh info on next open
    };
    actions.appendChild(btn);
    return true;
  }
  const obs = new MutationObserver(() => { injectToggle(); });
  obs.observe(document.body, {childList: true, subtree: true});
  setTimeout(injectToggle, 1500);
})();
</script>
"""
