"""Barcode + VIN scanning — camera-based identification for parts and vehicles."""
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
<style>
#scanModal{display:none;position:fixed;inset:0;background:#000;z-index:9999;overflow:auto;color:#fff;}
#scanInner{max-width:700px;margin:0 auto;padding:16px;min-height:100vh;}
.scanBtn{width:100%;padding:14px;border:none;border-radius:10px;font-weight:700;
font-size:15px;cursor:pointer;margin-bottom:8px;}
.scanBtn.pink{background:#ec4899;color:#fff;}
.scanBtn.blue{background:#3b82f6;color:#fff;}
.scanBtn.dark{background:#1e2938;color:#fff;}
.scanBtn.green{background:#10b981;color:#fff;}
#scanVideo{width:100%;border-radius:12px;background:#000;max-height:60vh;object-fit:cover;}
.scanCard{background:#0f1520;border:1px solid #1e2938;border-radius:10px;padding:12px;margin-bottom:8px;color:#e6edf5;}
#scanResult{margin-top:10px;}
.scanHeader{display:flex;justify-content:space-between;align-items:center;padding-bottom:12px;
border-bottom:2px solid #1e2938;margin-bottom:14px;}
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
<button class="scanBtn pink" onclick="scanStart('part')">Scan Part Number</button>
<button class="scanBtn blue" onclick="scanStart('vin')">Scan VIN (Vehicle)</button>
<button class="scanBtn dark" onclick="scanManual('part')">Type Part Number</button>
<button class="scanBtn dark" onclick="scanManual('vin')">Type VIN</button>
</div>

<div id="scanCamera" style="display:none;">
<video id="scanVideo" autoplay muted playsinline></video>
<button class="scanBtn dark" style="margin-top:10px;" onclick="scanStop()">Stop Camera</button>
<div id="scanStatus" style="text-align:center;color:#7b8da3;font-size:13px;margin-top:8px;">Point camera at the barcode...</div>
</div>

<div id="scanResult"></div>
</div>
</div>

<script>
var _scanStream = null, _scanLoop = null, _scanMode = null;

function scanOpen(){document.getElementById('scanModal').style.display='block';scanReset();}
function scanClose(){scanStop();document.getElementById('scanModal').style.display='none';}
function scanReset(){
  document.getElementById('scanChoice').style.display='block';
  document.getElementById('scanCamera').style.display='none';
  document.getElementById('scanResult').innerHTML='';
  document.getElementById('scanStatus').textContent='Point camera at the barcode...';
}

async function scanStart(mode){
  _scanMode = mode;
  document.getElementById('scanChoice').style.display='none';
  document.getElementById('scanCamera').style.display='block';

  if(!('BarcodeDetector' in window)){
    document.getElementById('scanStatus').textContent='Barcode API not supported. Use Type instead.';
    return;
  }
  try {
    var formats = ['code_128','code_39','ean_13','ean_8','upc_a','upc_e','qr_code','codabar','itf'];
    var detector = new BarcodeDetector({formats: formats});

    _scanStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' }
    });
    var v = document.getElementById('scanVideo');
    v.srcObject = _scanStream;
    await v.play();

    _scanLoop = setInterval(async function(){
      try {
        var codes = await detector.detect(v);
        if(codes && codes.length){
          var val = codes[0].rawValue;
          scanStop();
          if(_scanMode==='part') scanLookupPart(val);
          else scanLookupVin(val);
        }
      } catch(e){}
    }, 400);

  } catch(e){
    document.getElementById('scanStatus').textContent='Camera error: '+e.message;
  }
}

function scanStop(){
  if(_scanLoop){clearInterval(_scanLoop);_scanLoop=null;}
  if(_scanStream){
    _scanStream.getTracks().forEach(function(t){t.stop();});
    _scanStream = null;
  }
  document.getElementById('scanCamera').style.display='none';
}

function scanManual(mode){
  var label = mode==='part'?'part number':'VIN (17 characters)';
  var val = prompt('Enter '+label+':');
  if(!val)return;
  _scanMode = mode;
  if(mode==='part') scanLookupPart(val);
  else scanLookupVin(val);
}

async function scanLookupPart(code){
  document.getElementById('scanResult').innerHTML = '<div class="scanCard">Looking up '+code+'...</div>';
  try {
    var r = await fetch('/api/scan/lookup-part/'+encodeURIComponent(code));
    var d = await r.json();
    var h = '<div class="scanCard">';
    h += '<div style="font-size:12px;color:#7b8da3;">SCANNED CODE</div>';
    h += '<div style="font-size:20px;font-weight:800;color:#ec4899;margin-bottom:10px;">'+d.code+'</div>';
    if(d.inventory && d.inventory.length){
      h += '<div style="font-weight:700;color:#10b981;margin-bottom:6px;">IN YOUR STOCK</div>';
      d.inventory.forEach(function(i){
        h += '<div style="padding:8px 0;border-top:1px solid #1e2938;">';
        h += '<b>'+(i.name||'-')+'</b><br>';
        h += '<span style="font-size:13px;color:#94a3b8;">Qty: '+i.qty+' | Sell: R'+(i.sell_price||0).toFixed(2)+'</span>';
        h += '</div>';
      });
    }
    if(d.catalog && d.catalog.length){
      h += '<div style="font-weight:700;color:#0ea5e9;margin:10px 0 6px;">IN CATALOG</div>';
      d.catalog.forEach(function(p){
        h += '<div style="padding:8px 0;border-top:1px solid #1e2938;">';
        h += '<b>'+(p.description||p.part_number||'-')+'</b>';
        h += '</div>';
      });
    }
    if(!d.found){
      h += '<div style="color:#f59e0b;margin-top:10px;">Not found in stock or catalog.</div>';
      h += '<button class="scanBtn green" style="margin-top:10px;" onclick="scanAddToPO(\''+d.code+'\')">Add to a Purchase Order</button>';
    }
    h += '<button class="scanBtn dark" style="margin-top:10px;" onclick="scanReset()">Scan Another</button>';
    h += '</div>';
    document.getElementById('scanResult').innerHTML = h;
  } catch(e){
    document.getElementById('scanResult').innerHTML = '<div class="scanCard" style="color:#ef4444;">Error: '+e.message+'</div>';
  }
}

async function scanLookupVin(vin){
  document.getElementById('scanResult').innerHTML = '<div class="scanCard">Decoding '+vin+'...</div>';
  try {
    var r = await fetch('/api/scan/lookup-vin/'+encodeURIComponent(vin));
    var d = await r.json();
    if(d.detail){
      document.getElementById('scanResult').innerHTML = '<div class="scanCard" style="color:#ef4444;">'+d.detail+'</div>';
      return;
    }
    var h = '<div class="scanCard">';
    h += '<div style="font-size:12px;color:#7b8da3;">VIN</div>';
    h += '<div style="font-size:16px;font-weight:800;color:#3b82f6;font-family:monospace;margin-bottom:10px;">'+d.vin+'</div>';
    h += '<div><b>Manufacturer:</b> '+d.manufacturer+'</div>';
    h += '<div><b>Country:</b> '+d.country+'</div>';
    h += '<div><b>Year:</b> '+d.year+'</div>';
    if(d.history && d.history.length){
      h += '<div style="font-weight:700;color:#10b981;margin:12px 0 6px;">WORKSHOP HISTORY ('+d.history.length+')</div>';
      d.history.forEach(function(j){
        h += '<div style="padding:6px 0;border-top:1px solid #1e2938;font-size:13px;">';
        h += '#'+j.id+' — '+(j.complaint||'').slice(0,50)+' — <b>'+j.status+'</b>';
        h += '</div>';
      });
    } else {
      h += '<div style="color:#7b8da3;margin-top:10px;">No previous workshop history for this vehicle.</div>';
    }
    h += '<button class="scanBtn dark" style="margin-top:10px;" onclick="scanReset()">Scan Another</button>';
    h += '</div>';
    document.getElementById('scanResult').innerHTML = h;
  } catch(e){
    document.getElementById('scanResult').innerHTML = '<div class="scanCard" style="color:#ef4444;">Error: '+e.message+'</div>';
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

function scanInjectParts(){
  var partsTab = document.getElementById('parts');
  if(!partsTab || document.getElementById('scanPartBtn')) return;
  var title = partsTab.querySelector('.panel-title');
  if(!title) return;
  var btn = document.createElement('button');
  btn.id = 'scanPartBtn';
  btn.className = 'btn';
  btn.style.cssText = 'background:linear-gradient(135deg,#ec4899,#be185d);margin-bottom:10px;';
  btn.textContent = '📷 Scan Part Barcode';
  btn.onclick = function(){ scanOpen(); setTimeout(function(){ scanStart('part'); }, 300); };
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
  btn.textContent = '📷 Scan VIN (door jamb or windscreen)';
  btn.onclick = function(){ scanOpen(); setTimeout(function(){ scanStart('vin'); }, 300); };
  title.parentNode.insertBefore(btn, title.nextSibling);
}

setInterval(function(){ scanInjectParts(); scanInjectVin(); }, 900);
setTimeout(function(){ scanInjectParts(); scanInjectVin(); }, 600);
document.getElementById('scanModal').addEventListener('click',function(e){if(e.target===this)scanClose();});
</script>
"""
