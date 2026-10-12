"""
Backup & Restore — export all workshop data to a single JSON file,
import it back with one tap if disaster strikes.

Protected by SUPER_ADMIN_PIN. Every backup is timestamped and signed
with the workshop_id, so you know exactly what you're restoring.

Routes:
  GET  /admin/backup               — download full JSON backup
  POST /api/backup/restore         — upload JSON, wipe + restore
  GET  /api/backup/info            — row counts per table (dry-run preview)
  GET  /api/backup/schedule/status — is the daily scheduler alive?

Scheduled backups: every 24h, saved to backups/ directory on disk.
Retains last 7 daily + last 4 weekly (rotates automatically).
"""
import os
import json
import shutil
import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse

router = APIRouter(tags=["backup"])

SUPER_ADMIN_PIN = os.getenv("SUPER_ADMIN_PIN", "").strip()
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/tmp/ramstech_backups"))

# Every table that gets backed up
BACKUP_TABLES = [
    "workshops",
    "jobs",
    "customers",
    "appointments",
    "quotes",
    "invoices",
    "inventory",
    "purchase_orders",
    "staff",
    "clockins",
    "expenses",
    "fuel_logs",
    "damage_reports",
]


def _require_admin(request: Request):
    pin = (request.query_params.get("pin") or
           request.headers.get("x-admin-pin") or "")
    if not SUPER_ADMIN_PIN or pin != SUPER_ADMIN_PIN:
        raise HTTPException(403, "Super-admin PIN required")
    return True


# ═══════════════════════════════════════════════════════════════
# BACKUP — dump all tables to a dict
# ═══════════════════════════════════════════════════════════════
def build_backup():
    """Return a complete snapshot dict of every table."""
    from main import store_list, MEM, _current_wid
    import db

    wid = _current_wid()
    snapshot = {
        "meta": {
            "version": 1,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "workshop_id": wid,
            "storage": "supabase" if db.is_ready() else "memory",
            "app": "RamsTech",
        },
        "tables": {},
    }

    for t in BACKUP_TABLES:
        try:
            # Temporarily set context to the admin's workshop for scoping
            rows = store_list(t)
            snapshot["tables"][t] = rows
        except Exception as e:
            snapshot["tables"][t] = []
            snapshot["meta"][f"error_{t}"] = str(e)

    total = sum(len(v) for v in snapshot["tables"].values())
    snapshot["meta"]["total_rows"] = total
    return snapshot


def save_backup_to_disk(snapshot):
    """Save a backup file to BACKUP_DIR with rotation."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = BACKUP_DIR / f"ramstech_{ts}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False)
    _rotate_backups()
    return fname


def _rotate_backups():
    """Keep last 7 daily + last 4 weekly, prune older."""
    try:
        files = sorted(BACKUP_DIR.glob("ramstech_*.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
    except Exception:
        return
    keep = set()
    # keep newest 7
    for f in files[:7]:
        keep.add(f)
    # keep 1 weekly for last 4 weeks (the oldest per 7-day bucket)
    weekly_seen = set()
    for f in files:
        try:
            d = datetime.fromtimestamp(f.stat().st_mtime)
        except Exception:
            continue
        week = d.strftime("%Y-W%W")
        if week not in weekly_seen and len(weekly_seen) < 4:
            weekly_seen.add(week)
            keep.add(f)
    # delete the rest
    for f in files:
        if f not in keep:
            try:
                f.unlink()
            except Exception:
                pass


def list_backups():
    """Return a list of backup files with metadata."""
    if not BACKUP_DIR.exists():
        return []
    out = []
    for f in sorted(BACKUP_DIR.glob("ramstech_*.json"),
                    key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            st = f.stat()
            with open(f, "r", encoding="utf-8") as fh:
                head = json.load(fh)
            out.append({
                "file": f.name,
                "size_kb": round(st.st_size / 1024, 1),
                "created": datetime.fromtimestamp(st.st_mtime)
                              .strftime("%Y-%m-%d %H:%M"),
                "total_rows": head.get("meta", {}).get("total_rows", 0),
                "storage": head.get("meta", {}).get("storage", "?"),
            })
        except Exception:
            continue
    return out


# ═══════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════
@router.get("/admin/backup")
def download_backup(request: Request):
    """Download the current full backup as a JSON file."""
    _require_admin(request)
    snapshot = build_backup()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ramstech_backup_{ts}.json"
    payload = json.dumps(snapshot, ensure_ascii=False, indent=2)
    return StreamingResponse(
        iter([payload]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/backup/info")
def backup_info(request: Request):
    _require_admin(request)
    from main import store_list
    counts = {}
    for t in BACKUP_TABLES:
        try:
            counts[t] = len(store_list(t))
        except Exception:
            counts[t] = -1
    return {
        "tables": counts,
        "total_rows": sum(v for v in counts.values() if v > 0),
        "storage_dir": str(BACKUP_DIR),
        "existing_backups": list_backups(),
    }


@router.get("/api/backup/list")
def list_saved_backups(request: Request):
    _require_admin(request)
    return {"count": len(list_backups()), "backups": list_backups()}


@router.post("/api/backup/save")
def save_now(request: Request):
    _require_admin(request)
    snapshot = build_backup()
    fname = save_backup_to_disk(snapshot)
    return {"success": True, "file": fname.name,
            "total_rows": snapshot["meta"]["total_rows"]}


@router.get("/api/backup/download/{filename}")
def download_saved(filename: str, request: Request):
    _require_admin(request)
    # prevent path traversal
    safe = os.path.basename(filename)
    path = BACKUP_DIR / safe
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "Backup file not found")
    with open(path, "r", encoding="utf-8") as f:
        payload = f.read()
    return StreamingResponse(
        iter([payload]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{safe}"'},
    )


@router.delete("/api/backup/{filename}")
def delete_backup(filename: str, request: Request):
    _require_admin(request)
    safe = os.path.basename(filename)
    path = BACKUP_DIR / safe
    if path.exists() and path.is_file():
        path.unlink()
        return {"success": True}
    raise HTTPException(404, "Not found")


# ═══════════════════════════════════════════════════════════════
# RESTORE
# ═══════════════════════════════════════════════════════════════
@router.post("/api/backup/restore")
async def restore_backup(request: Request, file: UploadFile = File(...)):
    """
    Replace all data with the contents of an uploaded backup file.
    Requires ?confirm=YES to prevent accidental wipes.
    """
    _require_admin(request)
    if request.query_params.get("confirm") != "YES":
        raise HTTPException(400, "Add ?confirm=YES to acknowledge data will be replaced")

    raw = await file.read()
    if len(raw) > 50 * 1024 * 1024:
        raise HTTPException(400, "Backup file too large (max 50 MB)")
    try:
        snapshot = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(400, "Invalid JSON backup")

    if not isinstance(snapshot, dict) or "tables" not in snapshot:
        raise HTTPException(400, "Not a RamsTech backup file")

    # safety: save current state as a pre-restore snapshot
    try:
        pre = build_backup()
        save_backup_to_disk(pre)
    except Exception:
        pass

    from main import store_save, store_delete, store_list, MEM
    import db

    stats = {}
    for table, rows in (snapshot.get("tables") or {}).items():
        if table not in BACKUP_TABLES:
            continue
        stats[table] = {"imported": 0, "deleted": 0, "errors": 0}

        # wipe existing rows
        try:
            existing = store_list(table)
            for r in existing:
                rid = r.get("id")
                if rid:
                    try:
                        store_delete(table, rid)
                        stats[table]["deleted"] += 1
                    except Exception:
                        pass
        except Exception:
            pass

        # insert restored rows
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            rid = row.get("id")
            if not rid:
                continue
            try:
                store_save(table, rid, row)
                stats[table]["imported"] += 1
            except Exception as e:
                stats[table]["errors"] += 1

    return {
        "success": True,
        "restored": stats,
        "source_backup": snapshot.get("meta", {}),
        "when": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ═══════════════════════════════════════════════════════════════
# Admin panel UI
# ═══════════════════════════════════════════════════════════════
BACKUP_HTML = """
<style>
  #rt-backup-panel {
    display: none; position: fixed; inset: 0; z-index: 9999;
    background: rgba(0,0,0,0.6); padding: 24px; overflow-y: auto;
  }
  #rt-backup-panel.open { display: block; }
  .rt-bk-modal {
    max-width: 640px; margin: 0 auto; background: #fff;
    border-radius: 14px; padding: 28px 28px 32px;
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    color: #1a1a1a; position: relative;
  }
  .rt-bk-close {
    position: absolute; top: 18px; right: 22px; background: none;
    border: none; font-size: 24px; cursor: pointer; color: #999;
  }
  .rt-bk-modal h2 { margin: 0 0 4px; font-size: 22px; letter-spacing: -0.5px; }
  .rt-bk-modal .sub { color: #777; font-size: 13px; margin: 0 0 20px; }
  .rt-bk-kpis {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 10px; margin-bottom: 20px;
  }
  .rt-bk-kpi {
    background: #fafafa; border: 1px solid #e5e5e5;
    border-radius: 10px; padding: 12px 14px;
  }
  .rt-bk-kpi .lbl {
    font-size: 10px; font-weight: 800; text-transform: uppercase;
    letter-spacing: 1px; color: #888; margin-bottom: 4px;
  }
  .rt-bk-kpi .val { font-size: 18px; font-weight: 900; }
  .rt-bk-actions {
    display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px;
  }
  .rt-bk-actions button, .rt-bk-actions a {
    padding: 11px 16px; border-radius: 8px; font-size: 13px;
    font-weight: 700; cursor: pointer; border: none;
    text-decoration: none; text-align: center;
  }
  .rt-bk-actions .primary { background: #16a34a; color: #fff; }
  .rt-bk-actions .dark { background: #111; color: #fff; }
  .rt-bk-actions .warn { background: #dc2626; color: #fff; }
  .rt-bk-actions .ghost {
    background: #fff; color: #111; border: 1px solid #ddd;
  }
  .rt-bk-section-title {
    font-size: 11px; font-weight: 800; letter-spacing: 1.5px;
    text-transform: uppercase; color: #666;
    margin: 24px 0 10px; padding-bottom: 6px;
    border-bottom: 1px solid #eee;
  }
  .rt-bk-list { display: flex; flex-direction: column; gap: 6px; }
  .rt-bk-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 14px; background: #fafafa;
    border-radius: 8px; font-size: 13px;
  }
  .rt-bk-item .meta { color: #888; font-size: 11px; }
  .rt-bk-item .acts { display: flex; gap: 6px; }
  .rt-bk-item .acts button {
    background: none; border: none; color: #666;
    font-size: 11px; font-weight: 700; cursor: pointer;
    padding: 3px 8px; border-radius: 5px;
  }
  .rt-bk-item .acts button:hover { background: #eee; }
  .rt-bk-item .acts button.dl { color: #16a34a; }
  .rt-bk-item .acts button.del { color: #dc2626; }
  .rt-bk-upload {
    background: #fef2f2; border: 2px dashed #fecaca;
    padding: 20px; border-radius: 10px; text-align: center;
    margin-top: 12px;
  }
  .rt-bk-upload input[type=file] { display: none; }
  .rt-bk-upload label {
    display: inline-block; padding: 10px 20px;
    background: #dc2626; color: #fff; border-radius: 8px;
    font-weight: 800; font-size: 13px; cursor: pointer;
  }
  .rt-bk-upload .warn-text {
    font-size: 12px; color: #991b1b; margin-top: 10px;
  }
  .rt-bk-msg {
    padding: 12px 14px; border-radius: 8px; font-size: 13px;
    margin-top: 12px; display: none;
  }
  .rt-bk-msg.on { display: block; }
  .rt-bk-msg.ok { background: #f0fdf4; color: #166534; }
  .rt-bk-msg.err { background: #fef2f2; color: #991b1b; }
  .rt-bk-restore-confirm {
    display: none; margin-top: 12px; padding: 14px;
    background: #fee2e2; border-radius: 8px; font-size: 13px;
    color: #991b1b;
  }
  .rt-bk-restore-confirm.on { display: block; }
  .rt-bk-restore-confirm button {
    margin-top: 10px; padding: 8px 14px;
    background: #dc2626; color: #fff; border: none;
    border-radius: 6px; font-weight: 800; cursor: pointer;
    font-size: 12px;
  }
</style>

<div id="rt-backup-panel" onclick="if(event.target===this)rtBkClose()">
  <div class="rt-bk-modal">
    <button class="rt-bk-close" onclick="rtBkClose()">×</button>
    <h2>Backup & Restore</h2>
    <p class="sub">Full data export. One-tap restore. Emergency insurance.</p>

    <div class="rt-bk-kpis" id="rt-bk-kpis"></div>

    <div class="rt-bk-actions">
      <button class="primary" onclick="rtBkDownloadNow()">⬇ Download backup now</button>
      <button class="dark" onclick="rtBkSaveNow()">💾 Save to server</button>
      <button class="ghost" onclick="rtBkRefresh()">↻ Refresh</button>
    </div>

    <div class="rt-bk-section-title">Saved backups</div>
    <div class="rt-bk-list" id="rt-bk-list">
      <div style="color:#888;font-size:13px;padding:10px">Loading…</div>
    </div>

    <div class="rt-bk-section-title" style="color:#dc2626;border-color:#fecaca">
      Restore from backup (danger zone)
    </div>
    <div class="rt-bk-upload">
      <label for="rt-bk-file">⬆ Upload backup file</label>
      <input type="file" id="rt-bk-file" accept=".json"
             onchange="rtBkFileSelected(this)">
      <div class="warn-text" id="rt-bk-file-name">
        Warning: restoring replaces ALL current data.
      </div>
      <div class="rt-bk-restore-confirm" id="rt-bk-confirm">
        <div id="rt-bk-confirm-text"></div>
        <button onclick="rtBkConfirmRestore()">Yes, wipe and restore</button>
      </div>
    </div>

    <div class="rt-bk-msg" id="rt-bk-msg"></div>
  </div>
</div>

<script>
(function(){
  let PIN = "";
  let PENDING_FILE = null;

  window.rtBkOpen = function(pin){
    PIN = pin || "";
    if (!PIN) {
      PIN = prompt("Super-admin PIN:");
      if (!PIN) return;
    }
    document.getElementById("rt-backup-panel").classList.add("open");
    rtBkRefresh();
  };
  window.rtBkClose = function(){
    document.getElementById("rt-backup-panel").classList.remove("open");
  };

  function qs(extra){
    const p = new URLSearchParams({pin: PIN});
    if (extra) for (const k in extra) p.set(k, extra[k]);
    return p.toString();
  }

  window.rtBkRefresh = async function(){
    try {
      const r = await fetch("/api/backup/info?" + qs());
      if (r.status === 403) { showMsg("err", "Invalid admin PIN"); return; }
      const d = await r.json();
      renderKpis(d);
      renderList(d.existing_backups || []);
    } catch(e) {
      showMsg("err", "Error: " + e.message);
    }
  };

  function renderKpis(d){
    const t = d.tables || {};
    const kpis = document.getElementById("rt-bk-kpis");
    const total = d.total_rows || 0;
    const tables = Object.keys(t).length;
    let html = `
      <div class="rt-bk-kpi"><div class="lbl">Total rows</div>
        <div class="val">${total.toLocaleString()}</div></div>
      <div class="rt-bk-kpi"><div class="lbl">Tables</div>
        <div class="val">${tables}</div></div>
      <div class="rt-bk-kpi"><div class="lbl">Backups saved</div>
        <div class="val">${(d.existing_backups || []).length}</div></div>
    `;
    kpis.innerHTML = html;
  }

  function renderList(list){
    const el = document.getElementById("rt-bk-list");
    if (!list.length){
      el.innerHTML = '<div style="color:#888;font-size:13px;padding:10px">No backups saved yet. Click "Save to server" to create the first.</div>';
      return;
    }
    el.innerHTML = list.map(b => `
      <div class="rt-bk-item">
        <div>
          <div style="font-weight:800">${esc(b.file)}</div>
          <div class="meta">${esc(b.created)} · ${b.size_kb} KB · ${b.total_rows} rows · ${esc(b.storage)}</div>
        </div>
        <div class="acts">
          <button class="dl" onclick="rtBkDownload('${esc(b.file)}')">Download</button>
          <button class="del" onclick="rtBkDelete('${esc(b.file)}')">Delete</button>
        </div>
      </div>
    `).join("");
  }

  window.rtBkDownloadNow = function(){
    window.location.href = "/admin/backup?" + qs();
  };

  window.rtBkSaveNow = async function(){
    showMsg("ok", "Saving…");
    try {
      const r = await fetch("/api/backup/save?" + qs(), {method: "POST"});
      const d = await r.json();
      if (!d.success) throw new Error(d.detail || "Failed");
      showMsg("ok", `✓ Saved ${d.file} (${d.total_rows} rows)`);
      rtBkRefresh();
    } catch(e) {
      showMsg("err", "Error: " + e.message);
    }
  };

  window.rtBkDownload = function(file){
    window.location.href = "/api/backup/download/" + encodeURIComponent(file) + "?" + qs();
  };

  window.rtBkDelete = async function(file){
    if (!confirm("Delete this backup file permanently?")) return;
    try {
      const r = await fetch("/api/backup/" + encodeURIComponent(file) + "?" + qs(),
                            {method: "DELETE"});
      if (!r.ok) throw new Error("Delete failed");
      rtBkRefresh();
    } catch(e) {
      showMsg("err", "Error: " + e.message);
    }
  };

  window.rtBkFileSelected = function(input){
    const f = input.files && input.files[0];
    if (!f) return;
    PENDING_FILE = f;
    document.getElementById("rt-bk-file-name").textContent =
      "Selected: " + f.name + " (" + Math.round(f.size / 1024) + " KB)";
    const c = document.getElementById("rt-bk-confirm");
    c.classList.add("on");
    document.getElementById("rt-bk-confirm-text").textContent =
      "Restoring will DELETE all current data and replace it with the contents of this file. This cannot be undone.";
  };

  window.rtBkConfirmRestore = async function(){
    if (!PENDING_FILE) return;
    const fd = new FormData();
    fd.append("file", PENDING_FILE);
    showMsg("ok", "Restoring… This may take a moment.");
    try {
      const r = await fetch("/api/backup/restore?" + qs({confirm: "YES"}), {
        method: "POST",
        body: fd,
      });
      const d = await r.json();
      if (!d.success) throw new Error(d.detail || "Restore failed");
      const counts = d.restored || {};
      const totalRestored = Object.values(counts).reduce((a, b) => a + (b.imported || 0), 0);
      showMsg("ok", `✓ Restored ${totalRestored} rows across ${Object.keys(counts).length} tables.`);
      document.getElementById("rt-bk-confirm").classList.remove("on");
      PENDING_FILE = null;
      rtBkRefresh();
    } catch(e) {
      showMsg("err", "Error: " + e.message);
    }
  };

  function showMsg(kind, text){
    const m = document.getElementById("rt-bk-msg");
    m.className = "rt-bk-msg on " + kind;
    m.textContent = text;
  }

  function esc(s){
    return String(s||"").replace(/[&<>"']/g, m => (
      {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
  }

  // Add a "Backup" link inside the admin panel
  function injectAdminLink(){
    const wrap = document.querySelector(".wrap");
    if (!wrap || document.getElementById("rt-bk-admin-link")) return;
    const link = document.createElement("a");
    link.id = "rt-bk-admin-link";
    link.href = "javascript:void(0)";
    link.textContent = "💾 Backup & Restore";
    link.style.cssText =
      "display:block;padding:14px 20px;background:#1a1a1a;color:#fff;" +
      "border:1px solid #2a2a2a;border-radius:12px;text-decoration:none;" +
      "margin-top:16px;font-weight:700;font-size:14px;text-align:center";
    link.onclick = function(){
      const stored = sessionStorage.getItem("rt_admin_pin");
      rtBkOpen(stored || "");
    };
    wrap.appendChild(link);
  }
  const obs = new MutationObserver(() => injectAdminLink());
  obs.observe(document.body, {childList: true, subtree: true});
  setTimeout(injectAdminLink, 800);
})();
</script>
"""
