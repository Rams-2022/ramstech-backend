"""Barcode + VIN scanning — with inline text input fallback."""
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


def _c():
    import db
    if not db.is_ready():
        raise HTTPException(503, "DB not ready")
    return db.get_client()


@router.get("/api/scan/lookup-part/{code}")
def lookup_part(code: str):
    code = code.strip().upper()
    c = _c()
    inv = c.table("inventory").select("*").ilike("part_number", f"%{code}%").execute().data or []
    parts = c.table("parts").select("*").ilike("part_number", f"%{code}%").execute().data or []
    return {"code": code, "inventory": inv, "catalog": parts, "found": len(inv) + len(parts) > 0}


@router.get("/api/scan/lookup-vin/{vin}")
def lookup_vin(vin: str):
    vin = vin.strip().upper()
    if len(vin) != 17:
        raise HTTPException(400, "VIN must be 17 characters")
    c = _c()
    jobs = c.table("jobs").select("id,created,customer,complaint,status,total")\
        .eq("registration", vin).order("created", desc=True).limit(20).execute().data or []
    jobs2 = c.table("jobs").select("id,created,customer,complaint,status,total")\
        .ilike("registration", f"%{vin}%").order("created", desc=True).limit(20).execute().data or []
    all_jobs = jobs + jobs2
    seen = set()
    unique_jobs = []
    for j in all_jobs:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique_jobs.append(j)

    try:
        from data import WMI_DB, YEAR_CODES
        m, ctry = WMI_DB.get(vin[:3], ("Unknown", "Unknown"))
        year = YEAR_CODES.get(vin[9], "Unknown")
    except Exception:
        m, ctry, year = "Unknown", "Unknown", "Unknown"

    return {
        "vin": vin,
        "manufacturer": m,
        "country": ctry,
        "year": year,
        "history": unique_jobs[:20],
    }


SCAN_HTML = r"""
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<style>
#scanModal{display:none;position:fixed;inset:0;background:#0a1018;z-index:9999;overflow:auto;color:#fff;}
#scanInner{max-width:700px;margin:0 auto;padding:16px;min-height:100vh;}
.scanBtn{width:100%;padding:14px;border:none;border-radius:10px;font-weight:700;
font-size:15px;cursor:pointer;margin-bottom:8px;text-decoration:none;display:block;text-align:center;}
.scanBtn.pink{background:#ec4899;color:#fff;}
.scanBtn.blue{background:#3b82f6;color:#fff;}
.scanBtn.dark{background:#1e2938;color:#fff;}
.scanBtn.green{background:#10b981;color:#fff;}
.scanBtn.orange{background:#f97316;color:#fff;}
#scanReader{width:100%;border-radius:12px;background:#000;overflow:hidden;}
#scanReader video{width:100% !important;height:auto !important;border-radius:12px;}
.scanCard{background:#0f1520;border:1px solid #1e2938;border-radius:10px;padding:12px;margin-bottom:8px;color:#e6edf5;}
#scanResult{margin-top:10px;}
.scanHeader{display:flex;justify-content:space-between;align-items:center;padding-bottom:12px;
border-bottom:2px solid #1e2938;margin-bottom:14px;}
.scanPin{width:100%;padding:14px;background:#0f1520;border:2px solid #1e2938;border-radius:10px;
color:#fff;font-size:18px;box-sizing:border-box;text-align:center;letter-spacing:2px;
font-family:monospace;margin:10px 0;text-transform:uppercase;}
.scanPin:focus{outline:none;border-color:#ec4899;}
.scanLabel{font-size:12px;color:#7b8da3;margin-bottom:6px;text-transform:uppercase;letter-spacing:1px;}
</style>

<div id="scanModal">
<div id="scanInner">
<div class="scanHeader">
<div>
<div style="font-size:11px;color:#7b8da3;letter-spacing:.5px;">WORKSHOP</div>
<div style="font-size:18px;font-weight:800;color:#ec4899;">Scan & Identify</div>
</div>
<button onclick="scanClose()" style="background:#1e2938;color:#fff;border:none;
border-radius:8px;padding:8px 14px;cursor:pointer;">X</button>
</div>

<div id="scanChoice">
<div class="scanCard">
<div class="scanLabel">VIN Lookup</div>
<input id="scanVinInput" class="scanPin" placeholder="17-character VIN" maxlength="17" autocapitalize="characters" autocomplete="off">
<button class="scanBtn blue" onclick="scanSubmitVin()">🔍 Look up VIN</button>
<button class="scanBtn dark" onclick="scanStart('vin')">📷 Try camera scan instead</button>
</div>

<div class="scanCard">
<div class="scanLabel">Part Lookup</div>
<input id="scanPartInput" class="scanPin" placeholder="Part number" autocomplete="off">
<button class="scanBtn pink" onclick="scanSubmitPart()">🔍 Look up Part</button>
<button class="scanBtn dark" onclick="scanStart('part')">📷 Try camera scan instead</button>
</div>
</div>

<div id="scanCamera" style="display:none;">
<div id="scanReader"></div>
<button class="scanBtn dark" style="margin-top:10px;" onclick="scanStop()">Stop Camera</button>
<div id="scanStatus" style="text-align:center;color:#7b8da3;font-size:13px;margin-top:8px;">Starting camera...</div>
</div>

<div id="scanResult"></div>
</div>
</div>

<script>
var _scanMode = null;
var _scanner = null;

function scanOpen(){
  document.getElementById('scanModal').style.display='block';
  scanReset();
  setTimeout(function(){ document.getElementById('scanVinInput').focus(); }, 300);
}
function scanClose(){
  scanStop();
  document.getElementById('scanModal').style.display='none';
}
function scanReset(){
  document.getElementById('scanChoice').style.display='block';
  document.getElementById('scanCamera').style.display='none';
  document.getElementById('scanResult').innerHTML='';
  var v = document.getElementById('scanVinInput'); if(v) v.value='';
  var p = document.getElementById('scanPartInput'); if(p) p.value='';
}

function scanSubmitVin(){
  var v = (document.getElementById('scanVinInput').value || '').trim().toUpperCase().replace(/[^A-Z0-9]/g,'');
  if(v.length !== 17){ alert('VIN must be 17 characters'); return; }
  scanLookupVin(v);
}

function scanSubmitPart(){
  var p = (document.getElementById('scanPartInput').value || '').trim().toUpperCase();
  if(!p){ alert('Enter a part number'); return; }
  scanLookupPart(p);
}

async function scanStart(mode){
  _scanMode = mode;
  document.getElementById('scanChoice').style.display='none';
  document.getElementById('scanCamera').style.display='block';
  document.getElementById('scanStatus').textContent = 'Starting camera...';

  if(typeof Html5Qrcode === 'undefined'){
    document.getElementById('scanStatus').textContent = 'Scanner library failed to load. Use text input above.';
    return;
  }

  try {
    _scanner = new Html5Qrcode("scanReader");
    var config = {
      fps: 12,
      qrbox: function(w, h){
        var size = Math.min(w, h) * 0.7;
        return { width: size, height: size * 0.6 };
      },
      aspectRatio: 1.7,
      formatsToSupport: mode === 'vin' ? [5, 3, 0, 1] : undefined
    };

    document.getElementById('scanStatus').textContent = 'Point camera at ' + (mode === 'vin' ? 'VIN barcode' : 'part barcode') + '...';

    await _scanner.start(
      { facingMode: 'environment' },
      config,
      function(decodedText){
        scanStop();
        if(_scanMode === 'part') scanLookupPart(decodedText);
        else scanLookupVin(decodedText);
      },
      function(){}
    );

  } catch(e){
    document.getElementById('scanStatus').textContent = 'Camera error: ' + e.message + '. Use text input above.';
  }
}

async function scanStop(){
  if(_scanner){
    try { await _scanner.stop(); _scanner.clear(); } catch(e){}
    _scanner = null;
  }
  document.getElementById('scanCamera').style.display='none';
}

async function scanLookupPart(code){
  document.getElementById('scanResult').innerHTML = '<div class="scanCard">Looking up ' + code + '...</div>';
  try {
    var r = await fetch('/api/scan/lookup-part/' + encodeURIComponent(code));
    var d = await r.json();
    var h = '<div class="scanCard">';
    h += '<div style="font-size:12px;color:#7b8da3;">PART NUMBER</div>';
    h += '<div style="font-size:20px;font-weight:800;color:#ec4899;margin-bottom:10px;">' + d.code + '</div>';
    if(d.inventory && d.inventory.length){
      h += '<div style="font-weight:700;color:#10b981;margin-bottom:6px;">IN YOUR STOCK</div>';
      d.inventory.forEach(function(i){
        h += '<div style="padding:8px 0;border-top:1px solid #1e2938;">';
        h += '<b>' + (i.name||'-') + '</b><br>';
        h += '<span style="font-size:13px;color:#94a3b8;">Qty: ' + i.qty + ' | Sell: R' + (i.sell_price||0).toFixed(2) + '</span>';
        h += '</div>';
      });
    }
    if(d.catalog && d.catalog.length){
      h += '<div style="font-weight:700;color:#0ea5e9;margin:10px 0 6px;">IN CATALOG</div>';
      d.catalog.forEach(function(p){
        h += '<div style="padding:8px 0;border-top:1px solid #1e2938;">';
        h += '<b>' + (p.description||p.part_number||'-') + '</b>';
        h += '</div>';
      });
    }
    if(!d.found){
      h += '<div style="color:#f59e0b;margin-top:10px;">Not found in stock or catalog.</div>';
      h += '<button class="scanBtn green" style="margin-top:10px;" onclick="scanAddToPO(\'' + d.code + '\')">Add to a Purchase Order</button>';
      h += '<button class="scanBtn orange" style="margin-top:6px;" onclick="scanSearchSupplier(\'' + d.code + '\')">🔍 Search AutoZone / Goldwagen / Midas</button>';
    } else {
      h += '<button class="scanBtn orange" style="margin-top:10px;" onclick="scanSearchSupplier(\'' + d.code + '\')">🔍 Search online suppliers for price</button>';
    }
    h += '<button class="scanBtn dark" style="margin-top:10px;" onclick="scanReset()">Back</button>';
    h += '</div>';
    document.getElementById('scanResult').innerHTML = h;
  } catch(e){
    document.getElementById('scanResult').innerHTML = '<div class="scanCard" style="color:#ef4444;">Error: ' + e.message + '</div>';
  }
}

async function scanLookupVin(vin){
  document.getElementById('scanResult').innerHTML = '<div class="scanCard">Decoding ' + vin + '...</div>';
  try {
    var r = await fetch('/api/scan/lookup-vin/' + encodeURIComponent(vin));
    var d = await r.json();
    if(d.detail){
      document.getElementById('scanResult').innerHTML = '<div class="scanCard" style="color:#ef4444;">' + d.detail + '</div>';
      return;
    }
    var h = '<div class="scanCard">';
    h += '<div style="font-size:12px;color:#7b8da3;">VIN</div>';
    h += '<div style="font-size:16px;font-weight:800;color:#3b82f6;font-family:monospace;margin-bottom:10px;">' + d.vin + '</div>';
    h += '<div><b>Manufacturer:</b> ' + d.manufacturer + '</div>';
    h += '<div><b>Country:</b> ' + d.country + '</div>';
    h += '<div><b>Year:</b> ' + d.year + '</div>';
    if(d.history && d.history.length){
      h += '<div style="font-weight:700;color:#10b981;margin:12px 0 6px;">WORKSHOP HISTORY (' + d.history.length + ')</div>';
      d.history.forEach(function(j){
        h += '<div style="padding:6px 0;border-top:1px solid #1e2938;font-size:13px;">';
        h += '#' + j.id + ' — ' + (j.complaint||'').slice(0,50) + ' — <b>' + j.status + '</b>';
        h += '</div>';
      });
    } else {
      h += '<div style="color:#7b8da3;margin-top:10px;">No previous workshop history for this vehicle.</div>';
    }
    h += '<button class="scanBtn green" style="margin-top:10px;" onclick="scanCreateJobFromVin(\'' + d.vin + '\',\'' + (d.manufacturer||'') + '\',\'' + (d.year||'') + '\')">➕ Create Job Card for this Vehicle</button>';
    h += '<button class="scanBtn dark" style="margin-top:6px;" onclick="scanReset()">Back</button>';
    h += '</div>';
    document.getElementById('scanResult').innerHTML = h;
  } catch(e){
    document.getElementById('scanResult').innerHTML = '<div class="scanCard" style="color:#ef4444;">Error: ' + e.message + '</div>';
  }
}

function scanCreateJobFromVin(vin, make, year){
  scanClose();
  if(typeof wfOpenNewQuote === 'function'){
    wfOpenNewQuote();
    setTimeout(function(){
      var vf = document.getElementById('wqReg');
      if(vf){ vf.value = vin; }
      var mk = document.getElementById('wqMake');
      if(mk){ mk.value = make; }
    }, 400);
  }
}

function scanAddToPO(part_number){
  scanClose();
  if(typeof poOpen==='function'){
    poOpen();
    setTimeout(function(){
      if(typeof poAddItem==='function'){
        poAddItem();
        setTimeout(function(){
          var idx = _poItems.length - 1;
          if(idx >= 0){
            _poItems[idx].part_number = part_number;
            if(typeof poRenderItems==='function') poRenderItems();
          }
        }, 200);
      }
    }, 500);
  }
}

function scanSearchSupplier(part_number){
  var pn = encodeURIComponent(part_number);
  var h = '<div class="scanCard">';
  h += '<div style="font-size:12px;color:#7b8da3;">SEARCH ONLINE</div>';
  h += '<div style="font-size:16px;font-weight:800;color:#f97316;margin-bottom:10px;">' + part_number + '</div>';
  h += '<a class="scanBtn orange" target="_blank" href="https://www.autozoneonline.co.za/search?q=' + pn + '">🔍 AutoZone</a>';
  h += '<a class="scanBtn green" target="_blank" href="https://www.goldwagen.com/?s=' + pn + '">🔍 Goldwagen</a>';
  h += '<a class="scanBtn blue" target="_blank" href="https://www.midas.co.za/search?q=' + pn + '">🔍 Midas</a>';
  h += '<a class="scanBtn pink" target="_blank" href="https://www.google.com/search?q=' + pn + '+car+part+South+Africa">🔍 Google Search</a>';
  h += '<button class="scanBtn dark" style="margin-top:10px;" onclick="scanReset()">Back</button>';
  h += '</div>';
  document.getElementById('scanResult').innerHTML = h;
}

function scanInjectParts(){
  var partsTab = document.getElementById('parts');
  if(!partsTab || document.getElementById('scanPartBtn')) return;
  var title = partsTab.querySelector('.panel-title');
  if(!title) return;
  var btn = document.createElement('button');
  btn.id = 'scanPartBtn';
  btn.className = 'btn';
  btn.style.cssText = 'background:linear-gradient(135deg,#ec4899,#be185d);margin-bottom:10px;';
  btn.textContent = '🔍 Look up Part (scan or type)';
  btn.onclick = function(){ scanOpen(); };
  title.parentNode.insertBefore(btn, title.nextSibling);
}

function scanInjectVin(){
  var vinTab = document.getElementById('vin');
  if(!vinTab || document.getElementById('scanVinBtn')) return;
  var title = vinTab.querySelector('.panel-title');
  if(!title) return;
  var btn = document.createElement('button');
  btn.id = 'scanVinBtn';
  btn.className = 'btn';
  btn.style.cssText = 'background:linear-gradient(135deg,#3b82f6,#1d4ed8);margin-bottom:10px;';
  btn.textContent = '🔍 Look up VIN (scan or type)';
  btn.onclick = function(){ scanOpen(); };
  title.parentNode.insertBefore(btn, title.nextSibling);
}

setInterval(function(){ scanInjectParts(); scanInjectVin(); }, 900);
setTimeout(function(){ scanInjectParts(); scanInjectVin(); }, 600);
document.getElementById('scanModal').addEventListener('click',function(e){if(e.target===this)scanClose();});
</script>
"""
