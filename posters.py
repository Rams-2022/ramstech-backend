"""
Social media poster generator.
Open the URLs on your phone, screenshot the square, post it.

Routes:
  /posters                 — index
  /posters/1..5            — the five posters
  ?size=story              — 9:16 vertical version for Stories/Status
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["posters"])


# ═══════════════════════════════════════════════════════════════
# SHARED CSS
# ═══════════════════════════════════════════════════════════════
def _css(size):
    ar = "9 / 16" if size == "story" else "1 / 1"
    maxw = "480px" if size == "story" else "640px"
    return f"""
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
      background: #0a0a0a; color: #fff; min-height: 100vh;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      padding: 20px 12px;
      -webkit-font-smoothing: antialiased;
    }}
    .tip {{
      position: fixed; top: 0; left: 0; right: 0;
      background: #16a34a; color: #fff; padding: 10px 16px;
      text-align: center; font-size: 12px; font-weight: 800;
      letter-spacing: 0.3px; z-index: 100;
      animation: fadeout 0.5s ease 3s forwards;
    }}
    @keyframes fadeout {{ to {{ opacity: 0; visibility: hidden; }} }}
    .poster {{
      aspect-ratio: {ar};
      width: min(100vw - 24px, {maxw});
      border-radius: 20px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      position: relative;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }}
    .nav {{
      display: flex; gap: 8px; margin-top: 20px;
      flex-wrap: wrap; justify-content: center;
    }}
    .nav a {{
      color: #888; text-decoration: none; font-size: 13px;
      padding: 8px 14px; border: 1px solid #333; border-radius: 8px;
      font-weight: 600;
    }}
    .nav a:hover {{ color: #fff; border-color: #fff; }}
    .nav a.on {{ background: #fff; color: #111; border-color: #fff; }}
    """


def _wrap(size, body, poster_class="dark"):
    """Common poster wrapper. Caller supplies the inner .poster content."""
    return f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RamsTech Poster</title>
<style>{_css(size)}</style>
</head><body>
<div class="tip">📸 Screenshot the square below — tip disappears in 3 seconds</div>

<div class="poster {poster_class}">
{body}
</div>

<div class="nav">
  <a href="/posters?size={'story' if size != 'story' else ''}">{"Square" if size == "story" else "Story"}</a>
  <a href="/posters">All posters</a>
</div>
</body></html>"""


# ═══════════════════════════════════════════════════════════════
# POSTER 1 — PAIN HOOK
# ═══════════════════════════════════════════════════════════════
@router.get("/posters/1", response_class=HTMLResponse)
def poster_1(size: str = ""):
    body = """
    <div style="flex:1;display:flex;flex-direction:column;
                justify-content:center;align-items:center;
                background:#0a0a0a;padding:8%;text-align:center">
      <div style="font-size:clamp(72px,18vw,160px);font-weight:900;
                  letter-spacing:-6px;line-height:0.95;color:#fff">
        R47,500
      </div>
      <div style="font-size:clamp(14px,3vw,20px);color:#888;
                  margin-top:5%;line-height:1.5;max-width:80%;
                  font-weight:500">
        That's what one SA workshop has sitting in overdue invoices right now.
      </div>
      <div style="margin-top:8%;font-size:clamp(16px,3.5vw,22px);
                  font-weight:900;color:#16a34a;letter-spacing:-0.3px">
        Is this you?
      </div>
    </div>
    <div style="background:#16a34a;color:#fff;padding:4% 6%;
                text-align:center;font-weight:800;
                font-size:clamp(13px,2.5vw,16px);
                letter-spacing:0.3px">
      RAMSTECH · Chases your money for you
    </div>
    """
    return HTMLResponse(_wrap(size, body))


# ═══════════════════════════════════════════════════════════════
# POSTER 2 — THE MONEY LOOP
# ═══════════════════════════════════════════════════════════════
@router.get("/posters/2", response_class=HTMLResponse)
def poster_2(size: str = ""):
    body = """
    <div style="flex:1;display:flex;flex-direction:column;
                justify-content:space-between;background:#fff;
                color:#111;padding:7%">
      <div>
        <div style="font-size:clamp(11px,2vw,13px);font-weight:800;
                    text-transform:uppercase;letter-spacing:2px;
                    color:#16a34a">
          HOW IT WORKS
        </div>
        <div style="font-size:clamp(22px,5.5vw,38px);font-weight:900;
                    letter-spacing:-1px;line-height:1.1;margin-top:2%">
          The money loop,<br>fully automated.
        </div>
      </div>

      <div style="display:flex;flex-direction:column;gap:3.5%">
        <!-- step 1 -->
        <div style="display:flex;gap:4%;align-items:center">
          <div style="flex-shrink:0;width:clamp(36px,8vw,48px);
                      height:clamp(36px,8vw,48px);border-radius:50%;
                      background:#f0fdf4;color:#16a34a;display:flex;
                      align-items:center;justify-content:center;
                      font-weight:900;font-size:clamp(16px,3vw,20px)">
            1
          </div>
          <div>
            <div style="font-weight:800;font-size:clamp(13px,2.6vw,16px)">
              Invoice goes overdue
            </div>
            <div style="color:#666;font-size:clamp(11px,2.2vw,13px);margin-top:2px">
              RamsTech notices it instantly
            </div>
          </div>
        </div>

        <!-- step 2 -->
        <div style="display:flex;gap:4%;align-items:center">
          <div style="flex-shrink:0;width:clamp(36px,8vw,48px);
                      height:clamp(36px,8vw,48px);border-radius:50%;
                      background:#f0fdf4;color:#16a34a;display:flex;
                      align-items:center;justify-content:center;
                      font-weight:900;font-size:clamp(16px,3vw,20px)">
            2
          </div>
          <div>
            <div style="font-weight:800;font-size:clamp(13px,2.6vw,16px)">
              WhatsApp sent automatically
            </div>
            <div style="color:#666;font-size:clamp(11px,2.2vw,13px);margin-top:2px">
              Friendly → firm → urgent as needed
            </div>
          </div>
        </div>

        <!-- step 3 -->
        <div style="display:flex;gap:4%;align-items:center">
          <div style="flex-shrink:0;width:clamp(36px,8vw,48px);
                      height:clamp(36px,8vw,48px);border-radius:50%;
                      background:#f0fdf4;color:#16a34a;display:flex;
                      align-items:center;justify-content:center;
                      font-weight:900;font-size:clamp(16px,3vw,20px)">
            3
          </div>
          <div>
            <div style="font-weight:800;font-size:clamp(13px,2.6vw,16px)">
              Customer taps the pay link
            </div>
            <div style="color:#666;font-size:clamp(11px,2.2vw,13px);margin-top:2px">
              Pays by card in 30 seconds
            </div>
          </div>
        </div>

        <!-- step 4 -->
        <div style="display:flex;gap:4%;align-items:center">
          <div style="flex-shrink:0;width:clamp(36px,8vw,48px);
                      height:clamp(36px,8vw,48px);border-radius:50%;
                      background:#16a34a;color:#fff;display:flex;
                      align-items:center;justify-content:center;
                      font-weight:900;font-size:clamp(16px,3vw,20px)">
            ✓
          </div>
          <div>
            <div style="font-weight:800;font-size:clamp(13px,2.6vw,16px)">
              Invoice marked paid
            </div>
            <div style="color:#666;font-size:clamp(11px,2.2vw,13px);margin-top:2px">
              No human input. Ever.
            </div>
          </div>
        </div>
      </div>

      <div style="border-top:1px solid #eee;padding-top:4%;
                  display:flex;justify-content:space-between;
                  align-items:center">
        <div style="font-weight:900;font-size:clamp(14px,3vw,18px);
                    letter-spacing:-0.5px">
          RAMSTECH
        </div>
        <div style="font-size:clamp(11px,2.2vw,13px);color:#666;
                    font-weight:600">
          15-min demo →
        </div>
      </div>
    </div>
    """
    return HTMLResponse(_wrap(size, body))


# ═══════════════════════════════════════════════════════════════
# POSTER 3 — FEATURE GRID
# ═══════════════════════════════════════════════════════════════
@router.get("/posters/3", response_class=HTMLResponse)
def poster_3(size: str = ""):
    def feat(icon, title, sub):
        return f"""
        <div style="background:#1a1a1a;border-radius:14px;padding:7% 6%;
                    border:1px solid #2a2a2a;display:flex;
                    flex-direction:column;justify-content:center">
          <div style="font-size:clamp(20px,4.5vw,30px);margin-bottom:8%">
            {icon}
          </div>
          <div style="font-weight:800;font-size:clamp(12px,2.4vw,15px);
                      line-height:1.25;margin-bottom:3%">
            {title}
          </div>
          <div style="color:#888;font-size:clamp(10px,1.9vw,12px);
                      line-height:1.4">
            {sub}
          </div>
        </div>
        """
    body = f"""
    <div style="flex:1;background:#0a0a0a;padding:6%;
                display:flex;flex-direction:column;gap:4%">
      <div>
        <div style="font-size:clamp(11px,2vw,13px);font-weight:800;
                    text-transform:uppercase;letter-spacing:2px;
                    color:#16a34a">
          EVERYTHING INSIDE
        </div>
        <div style="font-size:clamp(20px,4.8vw,32px);font-weight:900;
                    letter-spacing:-1px;line-height:1.1;margin-top:2%;
                    color:#fff">
          Built for how<br>workshops actually run.
        </div>
      </div>
      <div style="flex:1;display:grid;
                  grid-template-columns:1fr 1fr;
                  grid-template-rows:1fr 1fr 1fr;
                  gap:3.5%">
        {feat("💰", "Aged Debtors", "See who owes what — colour-coded by urgency")}
        {feat("💬", "WhatsApp Reminders", "Sent automatically. Tone matches how overdue.")}
        {feat("💳", "Pay-Now Links", "Customer taps, pays, invoice closes itself.")}
        {feat("⚙", "Auto-Reminders", "Chases everyone 30+ days while you sleep.")}
        {feat("🤖", "AI Diagnostics", "Photo a problem → get causes + steps.")}
        {feat("📊", "Profit Dashboard", "See which jobs and techs make money.")}
      </div>
    </div>
    """
    return HTMLResponse(_wrap(size, body))


# ═══════════════════════════════════════════════════════════════
# POSTER 4 — BEFORE / AFTER
# ═══════════════════════════════════════════════════════════════
@router.get("/posters/4", response_class=HTMLResponse)
def poster_4(size: str = ""):
    def row_left(text):
        return f"""
        <div style="display:flex;gap:3%;align-items:flex-start;
                    margin-bottom:6%">
          <div style="flex-shrink:0;width:18px;height:18px;
                      border-radius:50%;background:#fecaca;color:#dc2626;
                      display:flex;align-items:center;justify-content:center;
                      font-weight:900;font-size:11px">✕</div>
          <div style="font-size:clamp(11px,2.1vw,13px);color:#444;
                      line-height:1.4;font-weight:500">{text}</div>
        </div>
        """
    def row_right(text):
        return f"""
        <div style="display:flex;gap:3%;align-items:flex-start;
                    margin-bottom:6%">
          <div style="flex-shrink:0;width:18px;height:18px;
                      border-radius:50%;background:#16a34a;color:#fff;
                      display:flex;align-items:center;justify-content:center;
                      font-weight:900;font-size:11px">✓</div>
          <div style="font-size:clamp(11px,2.1vw,13px);color:#eee;
                      line-height:1.4;font-weight:500">{text}</div>
        </div>
        """
    body = f"""
    <div style="flex:1;display:grid;grid-template-columns:1fr 1fr">
      <!-- BEFORE -->
      <div style="background:#f5f5f5;color:#111;padding:6% 7%;
                  display:flex;flex-direction:column">
        <div style="font-size:clamp(10px,2vw,12px);font-weight:800;
                    text-transform:uppercase;letter-spacing:2px;
                    color:#999;margin-bottom:12%">
          BEFORE
        </div>
        {row_left("Sunday nights chasing payments by phone")}
        {row_left("'I'll pay next week' — that never comes")}
        {row_left("R47,000 sitting there. Untouched.")}
        {row_left("2 hours a week of admin you'll never get back")}
      </div>

      <!-- AFTER -->
      <div style="background:#0a0a0a;padding:6% 7%;
                  display:flex;flex-direction:column">
        <div style="font-size:clamp(10px,2vw,12px);font-weight:800;
                    text-transform:uppercase;letter-spacing:2px;
                    color:#16a34a;margin-bottom:12%">
          AFTER
        </div>
        {row_right("Reminders go out automatically")}
        {row_right("Customer taps a pay link. Done.")}
        {row_right("Money collected while you work")}
        {row_right("Zero admin. Zero awkward calls.")}
      </div>
    </div>
    <div style="background:#16a34a;color:#fff;padding:3.5% 6%;
                text-align:center;font-weight:900;
                font-size:clamp(12px,2.4vw,15px);letter-spacing:0.3px">
      RAMSTECH · See it on your own invoices — 15-min demo
    </div>
    """
    return HTMLResponse(_wrap(size, body))


# ═══════════════════════════════════════════════════════════════
# POSTER 5 — FOUNDING MEMBER OFFER
# ═══════════════════════════════════════════════════════════════
@router.get("/posters/5", response_class=HTMLResponse)
def poster_5(size: str = ""):
    body = """
    <div style="flex:1;background:#16a34a;color:#fff;padding:8%;
                display:flex;flex-direction:column;
                justify-content:space-between;text-align:center">
      <div>
        <div style="display:inline-block;background:#dc2626;color:#fff;
                    padding:4px 14px;border-radius:20px;
                    font-size:clamp(10px,2vw,12px);font-weight:900;
                    text-transform:uppercase;letter-spacing:1.5px">
          First 5 workshops only
        </div>
        <div style="font-size:clamp(18px,4vw,26px);font-weight:900;
                    letter-spacing:-0.8px;line-height:1.1;
                    margin-top:6%;color:#fff">
          FOUNDING<br>MEMBER OFFER
        </div>
      </div>

      <div>
        <div style="font-size:clamp(56px,14vw,110px);font-weight:900;
                    letter-spacing:-4px;line-height:0.95;color:#fff">
          R749
        </div>
        <div style="font-size:clamp(13px,2.6vw,16px);font-weight:700;
                    color:#dcfce7;margin-top:3%">
          per month · normally R1,499
        </div>
        <div style="font-size:clamp(11px,2.2vw,14px);color:#dcfce7;
                    margin-top:5%;line-height:1.5;font-weight:500">
          6 months. Free setup.<br>Cancel anytime.
        </div>
      </div>

      <div style="background:#0a0a0a;color:#fff;padding:4% 5%;
                  border-radius:12px;font-weight:800;
                  font-size:clamp(12px,2.5vw,15px);
                  letter-spacing:0.3px">
       WhatsApp 075 434 9233 → 
      </div>
    </div>
    """
    return HTMLResponse(_wrap(size, body))


# ═══════════════════════════════════════════════════════════════
# POSTER 6 — AGED DEBTORS DASHBOARD (real UI mockup)
# ═══════════════════════════════════════════════════════════════
@router.get("/posters/6", response_class=HTMLResponse)
def poster_6(size: str = ""):
    def row(name, age, amount, bucket_color, bucket_label):
        return f"""
        <div style="display:flex;justify-content:space-between;
                    align-items:center;padding:3.5% 0;
                    border-bottom:1px solid #f0f0f0">
          <div>
            <div style="font-weight:800;font-size:clamp(11px,2.2vw,14px);
                        color:#111">{name}</div>
            <div style="font-size:clamp(9px,1.8vw,11px);color:#888;
                        margin-top:2px">
              <span style="background:{bucket_color};color:#fff;
                           padding:1px 7px;border-radius:10px;
                           font-weight:700;font-size:clamp(8px,1.6vw,10px);
                           text-transform:uppercase;letter-spacing:0.3px">
                {bucket_label}
              </span>
            </div>
          </div>
          <div style="font-weight:900;font-size:clamp(12px,2.4vw,16px);
                      color:#111;font-variant-numeric:tabular-nums">
            R{amount}
          </div>
        </div>
        """
    body = f"""
    <div style="flex:1;background:#f5f5f5;padding:6% 5%;display:flex;
                flex-direction:column;overflow:hidden">
      <div style="text-align:center;margin-bottom:5%">
        <div style="font-size:clamp(10px,1.9vw,12px);color:#888;
                    font-weight:800;text-transform:uppercase;
                    letter-spacing:1.5px">
          RAMSTECH · AGED DEBTORS
        </div>
        <div style="font-size:clamp(22px,5vw,34px);font-weight:900;
                    letter-spacing:-1.2px;color:#111;margin-top:3%">
          You are owed
        </div>
        <div style="font-size:clamp(38px,9vw,64px);font-weight:900;
                    letter-spacing:-2px;color:#dc2626;
                    line-height:1;margin-top:1%">
          R47,500
        </div>
      </div>

      <div style="background:#fff;border-radius:14px;padding:4% 5%;
                  box-shadow:0 4px 16px rgba(0,0,0,0.06);flex:1;
                  display:flex;flex-direction:column">
        {row("Thabo Motors", "90+ days", "12,400", "#7f1d1d", "90+ days")}
        {row("Sipho Logistics", "60 days", "9,850", "#dc2626", "60 days")}
        {row("Auto Care SA", "30 days", "8,200", "#f59e0b", "30 days")}
        {row("Mike's Bakkie", "Current", "6,400", "#16a34a", "Current")}
        {row("Fleet Services", "90+ days", "5,900", "#7f1d1d", "90+ days")}
        {row("Johan Motors", "30 days", "4,750", "#f59e0b", "30 days")}
      </div>

      <div style="margin-top:4%;background:#16a34a;color:#fff;
                  padding:3.5% 5%;border-radius:10px;text-align:center;
                  font-weight:900;font-size:clamp(11px,2.2vw,14px);
                  letter-spacing:0.3px">
        💬 Chase all overdue → 1 tap
      </div>
    </div>
    """
    return HTMLResponse(_wrap(size, body))


# ═══════════════════════════════════════════════════════════════
# POSTER 7 — WHATSAPP REMINDER THREAD
# ═══════════════════════════════════════════════════════════════
@router.get("/posters/7", response_class=HTMLResponse)
def poster_7(size: str = ""):
    def bubble(text, side="left", time=""):
        if side == "right":
            bg, align, radius = "#dcf8c6", "flex-end", "14px 4px 14px 14px"
            color = "#111"
        else:
            bg, align, radius = "#fff", "flex-start", "4px 14px 14px 14px"
            color = "#111"
        return f"""
        <div style="display:flex;justify-content:{align};
                    margin-bottom:3%">
          <div style="max-width:80%;background:{bg};color:{color};
                      padding:3% 3.5%;border-radius:{radius};
                      font-size:clamp(10px,1.9vw,12px);line-height:1.5;
                      box-shadow:0 1px 2px rgba(0,0,0,0.08)">
            {text}
            <div style="font-size:clamp(8px,1.5vw,9px);color:#888;
                        margin-top:4px;text-align:right">{time}</div>
          </div>
        </div>
        """
    body = f"""
    <div style="flex:1;background:#0a0a0a;display:flex;
                flex-direction:column;overflow:hidden">
      <!-- Header -->
      <div style="background:#075e54;color:#fff;padding:4% 5%;
                  display:flex;align-items:center;gap:3%">
        <div style="width:clamp(28px,6vw,36px);height:clamp(28px,6vw,36px);
                    border-radius:50%;background:#25d366;color:#fff;
                    display:flex;align-items:center;justify-content:center;
                    font-weight:900;font-size:clamp(12px,2.4vw,16px)">R</div>
        <div>
          <div style="font-weight:800;font-size:clamp(11px,2.2vw,14px)">
            RamsTech Bot
          </div>
          <div style="font-size:clamp(9px,1.7vw,11px);opacity:0.85">
            Automated reminder
          </div>
        </div>
      </div>

      <!-- Chat area -->
      <div style="flex:1;background:#ece5dd;padding:5% 4%;
                  display:flex;flex-direction:column;justify-content:center">
        {bubble("Hi <b>Thabo Motors</b>, friendly reminder: your balance of <b>R12,400</b> is now 90+ days overdue. Please arrange payment or contact us to discuss a plan.", "left", "09:00")}
        {bubble("Pay now: ramstech.co.za/pay/abc123", "left", "09:00")}
        {bubble("✓✓ Paid R12,400", "right", "10:34")}
        {bubble("<b>Invoice abc123 — PAID</b><br>Thank you! Your account is now up to date.", "left", "10:34")}
      </div>

      <!-- Footer brand -->
      <div style="background:#16a34a;color:#fff;padding:4% 5%;
                  text-align:center">
        <div style="font-weight:900;font-size:clamp(11px,2.2vw,14px);
                    letter-spacing:0.5px">
          Zero phone calls. Zero chasing.
        </div>
        <div style="font-size:clamp(9px,1.8vw,11px);margin-top:2%;
                    opacity:0.9">
          RAMSTECH · Chases your money for you
        </div>
      </div>
    </div>
    """
    return HTMLResponse(_wrap(size, body))


# ═══════════════════════════════════════════════════════════════
# POSTER 8 — CUSTOMER PORTAL (phone screen mockup)
# ═══════════════════════════════════════════════════════════════
@router.get("/posters/8", response_class=HTMLResponse)
def poster_8(size: str = ""):
    body = """
    <div style="flex:1;background:linear-gradient(160deg,#0a0a0a 0%,#1a1a1a 100%);
                padding:6% 5%;display:flex;flex-direction:column;
                align-items:center;justify-content:center">
      <div style="font-size:clamp(10px,1.9vw,12px);color:#16a34a;
                  font-weight:800;text-transform:uppercase;
                  letter-spacing:1.8px;margin-bottom:5%;text-align:center">
        THE CUSTOMER'S VIEW
      </div>

      <!-- Phone frame -->
      <div style="width:min(70%,280px);background:#fff;border-radius:28px;
                  padding:5% 4%;box-shadow:0 20px 60px rgba(0,0,0,0.6)">

        <!-- Hero card -->
        <div style="background:#111;color:#fff;border-radius:16px;
                    padding:5% 5%;margin-bottom:3%">
          <div style="font-size:clamp(10px,1.9vw,12px);font-weight:800">
            Hi Thabo
          </div>
          <div style="font-size:clamp(8px,1.6vw,10px);color:#888;
                      margin-top:1%">
            Rams Auto · your account
          </div>
          <div style="margin-top:5%;padding-top:5%;
                      border-top:1px solid #333">
            <div style="font-size:clamp(7px,1.5vw,9px);color:#888;
                        font-weight:700;text-transform:uppercase;
                        letter-spacing:1px">
              Outstanding balance
            </div>
            <div style="font-size:clamp(20px,4.5vw,28px);font-weight:900;
                        letter-spacing:-1px;color:#f87171;margin-top:2%">
              R12,400
            </div>
          </div>
        </div>

        <!-- Invoice card -->
        <div style="background:#fafafa;border-radius:12px;padding:4%;
                    margin-bottom:2%">
          <div style="display:flex;justify-content:space-between;
                      align-items:center;margin-bottom:4%">
            <div>
              <div style="font-size:clamp(9px,1.7vw,11px);font-weight:800">
                #abc123
              </div>
              <div style="font-size:clamp(7px,1.5vw,9px);color:#888">
                Due 30 Sep
              </div>
            </div>
            <div style="font-size:clamp(11px,2.2vw,14px);font-weight:900;
                        color:#dc2626">
              R12,400
            </div>
          </div>
          <div style="background:#fecaca;color:#991b1b;display:inline-block;
                      padding:2px 8px;border-radius:10px;
                      font-size:clamp(7px,1.4vw,9px);font-weight:800;
                      text-transform:uppercase;letter-spacing:0.5px">
            Overdue
          </div>
          <div style="margin-top:4%;background:#16a34a;color:#fff;
                      padding:3.5%;border-radius:8px;text-align:center;
                      font-weight:800;font-size:clamp(9px,1.8vw,11px)">
            Pay R12,400 now
          </div>
        </div>

        <!-- Book service card -->
        <div style="background:#f0fdf4;border-radius:12px;padding:4%;
                    text-align:center">
          <div style="font-size:clamp(8px,1.6vw,10px);color:#166534;
                      font-weight:800">
            📅 Book your next service
          </div>
        </div>
      </div>

      <div style="margin-top:6%;text-align:center;color:#fff">
        <div style="font-size:clamp(12px,2.4vw,16px);font-weight:900;
                    letter-spacing:-0.3px">
          Every customer gets their own portal.
        </div>
        <div style="font-size:clamp(9px,1.8vw,11px);color:#888;
                    margin-top:2%">
          Powered by RAMSTECH
        </div>
      </div>
    </div>
    """
    return HTMLResponse(_wrap(size, body))


# ═══════════════════════════════════════════════════════════════
# POSTER 9 — PROFIT DASHBOARD
# ═══════════════════════════════════════════════════════════════
@router.get("/posters/9", response_class=HTMLResponse)
def poster_9(size: str = ""):
    def kpi(label, value, color="#111"):
        return f"""
        <div style="background:#fafafa;border:1px solid #e5e5e5;
                    border-radius:10px;padding:5% 4%">
          <div style="font-size:clamp(7px,1.5vw,9px);font-weight:800;
                      text-transform:uppercase;letter-spacing:1px;
                      color:#888">{label}</div>
          <div style="font-size:clamp(14px,3vw,20px);font-weight:900;
                      letter-spacing:-0.7px;color:{color};
                      margin-top:3%">{value}</div>
        </div>
        """
    def bar(label, value, pct, color="#16a34a"):
        return f"""
        <div style="display:flex;align-items:center;gap:3%;
                    margin-bottom:3.5%">
          <div style="font-size:clamp(9px,1.8vw,11px);font-weight:700;
                      width:30%;color:#333">{label}</div>
          <div style="flex:1;height:6px;background:#f0f0f0;
                      border-radius:4px;overflow:hidden">
            <div style="width:{pct}%;height:100%;background:{color};
                        border-radius:4px"></div>
          </div>
          <div style="font-size:clamp(9px,1.8vw,11px);font-weight:800;
                      color:#111;min-width:60px;text-align:right;
                      font-variant-numeric:tabular-nums">{value}</div>
        </div>
        """
    body = f"""
    <div style="flex:1;background:#fff;padding:6% 5%;display:flex;
                flex-direction:column">
      <div style="font-size:clamp(9px,1.9vw,12px);color:#16a34a;
                  font-weight:800;text-transform:uppercase;
                  letter-spacing:1.8px">
        PROFIT DASHBOARD
      </div>
      <div style="font-size:clamp(20px,4.5vw,30px);font-weight:900;
                  letter-spacing:-1px;color:#111;margin-top:2%;
                  line-height:1.1">
        Which jobs actually<br>make you money?
      </div>

      <!-- KPI grid -->
      <div style="display:grid;grid-template-columns:1fr 1fr;
                  gap:3%;margin-top:5%">
        {kpi("Revenue", "R284,500")}
        {kpi("Total cost", "R198,200")}
        {kpi("Gross profit", "R86,300", "#16a34a")}
        {kpi("Avg margin", "30.3%", "#16a34a")}
      </div>

      <!-- By tech -->
      <div style="margin-top:6%;font-size:clamp(9px,1.9vw,12px);
                  font-weight:900;color:#111;
                  text-transform:uppercase;letter-spacing:1px">
        Profit by technician
      </div>
      <div style="margin-top:3%">
        {bar("Sipho M.", "R34,200", 85)}
        {bar("Thabo K.", "R28,900", 72)}
        {bar("Johan v.", "R15,300", 38)}
        {bar("Bongani N.", "R7,900", 20, "#dc2626")}
      </div>

      <!-- Bottom CTA -->
      <div style="margin-top:auto;padding-top:5%">
        <div style="background:#111;color:#fff;border-radius:10px;
                    padding:4% 5%;text-align:center">
          <div style="font-weight:900;font-size:clamp(11px,2.2vw,14px)">
            Know exactly where your money goes.
          </div>
          <div style="font-size:clamp(9px,1.8vw,11px);color:#888;
                      margin-top:2%">
            RAMSTECH · 15-min demo
          </div>
        </div>
      </div>
    </div>
    """
    return HTMLResponse(_wrap(size, body))


# ═══════════════════════════════════════════════════════════════
# POSTER 10 — FULL FEATURE STACK (everything at a glance)
# ═══════════════════════════════════════════════════════════════
@router.get("/posters/10", response_class=HTMLResponse)
def poster_10(size: str = ""):
    def item(icon, title, sub):
        return f"""
        <div style="display:flex;gap:3%;align-items:flex-start;
                    padding:3% 0;border-bottom:1px solid #f0f0f0">
          <div style="flex-shrink:0;font-size:clamp(16px,3.2vw,22px);
                      width:8%">{icon}</div>
          <div style="flex:1">
            <div style="font-weight:800;
                        font-size:clamp(11px,2.2vw,13px);
                        color:#111">{title}</div>
            <div style="font-size:clamp(9px,1.8vw,11px);color:#666;
                        margin-top:1px;line-height:1.4">{sub}</div>
          </div>
        </div>
        """
    body = f"""
    <div style="flex:1;background:#fff;padding:6% 5%;
                display:flex;flex-direction:column">
      <div style="font-size:clamp(9px,1.9vw,12px);color:#16a34a;
                  font-weight:800;text-transform:uppercase;
                  letter-spacing:1.8px">
        EVERYTHING IN RAMSTECH
      </div>
      <div style="font-size:clamp(20px,4.5vw,30px);font-weight:900;
                  letter-spacing:-1.2px;color:#111;margin-top:2%;
                  line-height:1.05">
        One app.<br>Runs the whole shop.
      </div>

      <div style="margin-top:4%;flex:1;overflow:hidden">
        {item("💰", "Aged Debtors Report", "Who owes what — colour-coded by how overdue")}
        {item("💬", "WhatsApp Reminders", "Sent automatically with tone that matches urgency")}
        {item("💳", "Pay-Now Links", "Yoco / PayFast / Stripe. Customer taps, pays.")}
        {item("⚙", "Auto-Reminder Scheduler", "Chases everyone 30+ days overdue. You sleep.")}
        {item("🔗", "Customer Portal", "Self-serve invoices, payments, and bookings")}
        {item("📊", "Profit Dashboard", "Which jobs, techs, and services actually make money")}
        {item("🤖", "AI Diagnostics", "Photo a problem → causes, steps, safety warnings")}
        {item("🎨", "AI Paint Match", "Snap the panel → colour codes + mixing formula")}
        {item("🔧", "VIN + Fault Codes", "Decode any VIN, search any DTC")}
        {item("📱", "Works Offline", "Install to home screen. Works on any phone.")}
      </div>

      <div style="margin-top:5%;background:#111;color:#fff;
                  padding:4% 5%;border-radius:10px;
                  display:flex;justify-content:space-between;
                  align-items:center">
        <div>
          <div style="font-weight:900;font-size:clamp(12px,2.4vw,15px)">
            RAMSTECH
          </div>
          <div style="font-size:clamp(8px,1.6vw,10px);color:#888;
                      margin-top:1px">
            Built for SA workshops
          </div>
        </div>
        <div style="background:#16a34a;color:#fff;padding:2.5% 5%;
                    border-radius:8px;font-weight:800;
                    font-size:clamp(9px,1.8vw,11px)">
          15-min demo →
        </div>
      </div>
    </div>
    """
    return HTMLResponse(_wrap(size, body))


# ═══════════════════════════════════════════════════════════════
# INDEX
# ═══════════════════════════════════════════════════════════════
@router.get("/posters", response_class=HTMLResponse)
def posters_index(size: str = ""):
    qs = "?size=story" if size == "story" else ""
    return HTMLResponse(f"""<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RamsTech Posters</title>
<style>
body{{font-family:-apple-system,sans-serif;background:#111;color:#fff;
  padding:30px 20px;max-width:520px;margin:0 auto}}
h1{{font-size:22px;margin:0 0 6px;letter-spacing:-0.5px}}
p{{color:#888;font-size:13px;margin:0 0 24px}}
h2{{font-size:11px;text-transform:uppercase;letter-spacing:2px;
  color:#16a34a;font-weight:800;margin:24px 0 10px}}
a{{display:block;padding:14px 18px;background:#1a1a1a;
  border:1px solid #2a2a2a;border-radius:12px;
  text-decoration:none;color:#fff;margin-bottom:8px;
  font-weight:600;font-size:14px}}
a:hover{{background:#222;border-color:#444}}
a .sub{{display:block;color:#888;font-size:12px;
  font-weight:400;margin-top:3px}}
.toggle{{display:flex;gap:8px;margin-bottom:12px}}
.toggle a{{flex:1;text-align:center;padding:10px;margin:0;
  font-size:13px;font-weight:700}}
.toggle a.on{{background:#fff;color:#111;border-color:#fff}}
</style></head><body>
<h1>RamsTech Posters</h1>
<p>Screenshot the poster. Post it. Repeat.</p>

<div class="toggle">
  <a href="/posters" class="{'on' if size != 'story' else ''}">Square (feed)</a>
  <a href="/posters?size=story" class="{'on' if size == 'story' else ''}">Story (9:16)</a>
</div>

<h2>Hooks &amp; Offers</h2>
<a href="/posters/1{qs}">1. Pain Hook
  <span class="sub">"R47,500 sitting in overdue invoices" — highest converting</span>
</a>
<a href="/posters/4{qs}">4. Before / After
  <span class="sub">Split-screen. Best for shares and comments.</span>
</a>
<a href="/posters/5{qs}">5. Founding Member Offer
  <span class="sub">R749/mo. First 5 workshops. Urgency + price.</span>
</a>

<h2>Show the app</h2>
<a href="/posters/6{qs}">6. Aged Debtors Dashboard
  <span class="sub">Real UI mockup — shows the money view</span>
</a>
<a href="/posters/7{qs}">7. WhatsApp Thread
  <span class="sub">The customer's side. Proves it works.</span>
</a>
<a href="/posters/8{qs}">8. Customer Portal
  <span class="sub">Phone mockup — the self-serve experience</span>
</a>
<a href="/posters/9{qs}">9. Profit Dashboard
  <span class="sub">Shows which techs make money. Visual, punchy.</span>
</a>

<h2>The full pitch</h2>
<a href="/posters/2{qs}">2. How It Works
  <span class="sub">The 4-step money loop, visualised</span>
</a>
<a href="/posters/3{qs}">3. Feature Grid
  <span class="sub">6 features. Shows the depth.</span>
</a>
<a href="/posters/10{qs}">10. Full Feature Stack
  <span class="sub">All 10 features in one poster. Best for closing.</span>
</a>
</body></html>""")
