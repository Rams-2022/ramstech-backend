"""Parts search — find any part by number, description, or supplier code."""
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


def _c():
    import db
    if not db.is_ready():
        raise HTTPException(503, "DB not ready")
    return db.get_client()


@router.get("/api/parts-search")
def search_parts(q: str = None, category: str = None, limit: int = 50):
    c = _c()
    results = []

    try:
        inv_q = c.table("inventory").select("*")
        if q:
            inv_q = inv_q.or_(f"part_number.ilike.%{q}%,name.ilike.%{q}%,supplier.ilike.%{q}%")
        if category:
            inv_q = inv_q.eq("category", category)
        inv = inv_q.limit(limit).execute().data or []
        for i in inv:
            results.append({
                "source": "inventory",
                "id": i.get("id"),
                "part_number": i.get("part_number", ""),
                "name": i.get("name", ""),
                "category": i.get("category", ""),
                "qty": i.get("qty", 0),
                "min_qty": i.get("min_qty", 5),
                "cost_price": i.get("cost_price", 0),
                "sell_price": i.get("sell_price", 0),
                "supplier": i.get("supplier", ""),
            })
    except Exception as e:
        print(f"[parts-search] inventory error: {e}")

    try:
        cat_q = c.table("parts").select("*")
        if q:
            cat_q = cat_q.or_(f"part_number.ilike.%{q}%,description.ilike.%{q}%")
        if category:
            cat_q = cat_q.eq("category", category)
        cat = cat_q.limit(limit).execute().data or []
        for p in cat:
            results.append({
                "source": "catalog",
                "id": p.get("id"),
                "part_number": p.get("part_number", ""),
                "name": p.get("description", ""),
                "category": p.get("category", ""),
                "qty": 0,
                "min_qty": 0,
                "cost_price": 0,
                "sell_price": 0,
                "supplier": "",
            })
    except Exception as e:
        print(f"[parts-search] catalog error: {e}")

    return {"query": q or "", "count": len(results), "results": results}


@router.get("/api/parts-search/{part_number}")
def lookup_exact(part_number: str):
    c = _c()
    pn = part_number.strip()
    inv = c.table("inventory").select("*").ilike("part_number", pn).execute().data or []
    cat = c.table("parts").select("*").ilike("part_number", pn).execute().data or []
    return {
        "part_number": pn,
        "inventory": inv,
        "catalog": cat,
        "found": len(inv) + len(cat) > 0,
    }


@router.get("/api/parts-search-categories")
def list_categories():
    c = _c()
    try:
        inv = c.table("inventory").select("category").execute().data or []
        cats = sorted(set([i.get("category", "") for i in inv if i.get("category")]))
    except Exception:
        cats = []
    return {"categories": cats}


PARTS_SEARCH_HTML = r"""
<style>
#psModal{display:none;position:fixed;inset:0;background:#0a1018;z-index:9999;overflow:auto;}
#psInner{max-width:700px;margin:0 auto;padding:16px;color:#e6edf5;min-height:100vh;}
.psHeader{display:flex;justify-content:space-between;align-items:center;padding-bottom:12px;
border-bottom:2px solid #1e2938;margin-bottom:14px;}
.psIn{width:100%;padding:14px 16px;background:#0f1520;border:2px solid #1e2938;border-radius:12px;
color:#e6edf5;font-size:16px;box-sizing:border-box;font-family:monospace;margin-bottom:10px;}
.psIn:focus{outline:none;border-color:#f97316;}
.psBtn{width:100%;padding:14px;background:#f97316;color:#fff;border:none;border-radius:10px;
font-weight:700;font-size:15px;cursor:pointer;margin-bottom:8px;}
.psBtn.dark{background:#1e2938;}
.psResult{background:#0f1520;border:1px solid #1e2938;border-radius:10px;
padding:12px;margin-bottom:8px;cursor:pointer;}
.psResult:active{background:#1e2938;}
.psPartNum{font-family:monospace;font-size:13px;color:#f97316;font-weight:700;}
.psName{font-size:15px;font-weight:700;margin:4px 0;}
.psMeta{font-size:12px;color:#94a3b8;}
.psStock{display:inline-block;padding:3px 10px;border-radius:12px;
font-size:11px;font-weight:700;color:#fff;background:#6b7280;margin-left:6px;}
.psStock.ok{background:#10b981;}
.psStock.low{background:#ef4444;}
.psStock.catalog{background:#0ea5e9;}
#psCount{font-size:12px;color:#7b8da3;margin-bottom:8px;}
.psEmpty{text-align:center;padding:40px 20px;color:#7b8da3;font-size:14px;}
</style>

<div id="psModal">
<div id="psInner">
<div class="psHeader">
<div>
<div style="font-size:11px;color:#7b8da3;letter-spacing:.5px;">WORKSHOP</div>
<div style="font-size:18px;font-weight:800;color:#f97316;">Search Parts</div>
</div>
<button onclick="psClose()" style="background:#1e2938;color:#fff;border:none;
border-radius:8px;padding:8px 14px;cursor:pointer;">X</button>
</div>

<input id="psQuery" class="psIn" placeholder="Enter part number or description..."
  autocapitalize="characters" autocomplete="off"
  onkeypress="if(event.key==='Enter')psSearch()">
<div style="display:flex;gap:8px;margin-bottom:12px;">
<button class="psBtn" style="flex:1;margin:0;" onclick="psSearch()">Search</button>
<button class="psBtn dark" style="flex:1;margin:0;" onclick="document.getElementById('psQuery').value='';psSearch()">Clear</button>
</div>

<div id="psCount"></div>
<div id="psResults"></div>
</div>
</div>

<script>
function psOpen(){
  document.getElementById('psModal').style.display='block';
  setTimeout(function(){document.getElementById('psQuery').focus();},200);
  psSearch();
}
function psClose(){document.getElementById('psModal').style.display='none';}

async function psSearch(){
  var q = document.getElementById('psQuery').value.trim();
  document.getElementById('psResults').innerHTML = '<div class="psEmpty">Searching...</div>';
  try {
    var url = q ? '/api/parts-search?q='+encodeURIComponent(q) : '/api/parts-search';
    var r = await fetch(url);
    var d = await r.json();
    psRender(d);
  } catch(e){
    document.getElementById('psResults').innerHTML = '<div class="psEmpty" style="color:#ef4444;">Error: '+e.message+'</div>';
  }
}

function psRender(d){
  var count = d.count || 0;
  document.getElementById('psCount').textContent = count > 0 ? (count + ' result' + (count === 1 ? '' : 's')) : '';
  if(!d.results || d.results.length === 0){
    document.getElementById('psResults').innerHTML = '<div class="psEmpty">No parts found. Try a different search or scan a barcode.</div>';
    return;
  }
  var h = '';
  d.results.forEach(function(p){
    var badge = '';
    if(p.source === 'catalog'){
      badge = '<span class="psStock catalog">CATALOG</span>';
    } else {
      var qty = parseInt(p.qty) || 0;
      var min = parseInt(p.min_qty) || 5;
      if(qty <= min) badge = '<span class="psStock low">'+qty+' in stock</span>';
      else badge = '<span class="psStock ok">'+qty+' in stock</span>';
    }
    var pjson = encodeURIComponent(JSON.stringify(p));
    h += '<div class="psResult" onclick="psDetail(decodeURIComponent(\''+pjson+'\'))">';
    h += '<div class="psPartNum">'+(p.part_number || '(no part number)')+badge+'</div>';
    h += '<div class="psName">'+(p.name || '(no description)')+'</div>';
    if(p.category) h += '<div class="psMeta">Category: '+p.category+'</div>';
    if(p.source === 'inventory'){
      h += '<div class="psMeta">Cost: R'+(p.cost_price||0).toFixed(2)+' | Sell: R'+(p.sell_price||0).toFixed(2)+'</div>';
      if(p.supplier) h += '<div class="psMeta">Supplier: '+p.supplier+'</div>';
    }
    h += '</div>';
  });
  document.getElementById('psResults').innerHTML = h;
}

function psDetail(jsonStr){
  var p = JSON.parse(jsonStr);
  var h = '<div style="background:#0f1520;border:2px solid #f97316;border-radius:10px;padding:14px;">';
  h += '<div style="font-size:11px;color:#7b8da3;">PART NUMBER</div>';
  h += '<div style="font-family:monospace;font-size:18px;font-weight:800;color:#f97316;margin-bottom:8px;">'+(p.part_number||'-')+'</div>';
  h += '<div style="font-size:16px;font-weight:700;margin-bottom:10px;">'+(p.name||'-')+'</div>';
  if(p.source === 'inventory'){
    h += '<div style="padding:6px 0;border-bottom:1px solid #1e2938;"><b>Qty on hand:</b> '+p.qty+'</div>';
    h += '<div style="padding:6px 0;border-bottom:1px solid #1e2938;"><b>Min stock:</b> '+p.min_qty+'</div>';
    h += '<div style="padding:6px 0;border-bottom:1px solid #1e2938;"><b>Cost price:</b> R'+(p.cost_price||0).toFixed(2)+'</div>';
    h += '<div style="padding:6px 0;border-bottom:1px solid #1e2938;"><b>Sell price:</b> R'+(p.sell_price||0).toFixed(2)+'</div>';
    if(p.supplier) h += '<div style="padding:6px 0;border-bottom:1px solid #1e2938;"><b>Supplier:</b> '+p.supplier+'</div>';
  } else {
    h += '<div style="padding:6px 0;color:#0ea5e9;">This part is in the catalog but not in your stock.</div>';
  }
  h += '<div style="display:flex;gap:6px;margin-top:12px;flex-wrap:wrap;">';
  var pnSafe = (p.part_number||'').replace(/'/g,'');
  var nameSafe = (p.name||'').replace(/'/g,'');
  h += '<button class="psBtn" style="flex:1;margin:0;padding:10px;font-size:13px;" onclick="psAddToPO(\''+pnSafe+'\',\''+nameSafe+'\','+(p.cost_price||0)+')">Add to Purchase Order</button>';
  h += '<button class="psBtn dark" style="flex:1;margin:0;padding:10px;font-size:13px;" onclick="psSearch()">Back</button>';
  h += '</div></div>';
  document.getElementById('psResults').innerHTML = h;
}

function psAddToPO(pn, name, cost){
  psClose();
  if(typeof poOpen === 'function'){
    poOpen();
    setTimeout(function(){
      if(typeof poAddItem === 'function'){
        poAddItem();
        setTimeout(function(){
          var idx = _poItems.length - 1;
          if(idx >= 0){
            _poItems[idx].part_number = pn;
            _poItems[idx].description = name;
            _poItems[idx].unit_price = cost;
            if(typeof poRenderItems === 'function') poRenderItems();
          }
        }, 200);
      }
    }, 500);
  }
}

function psInjectIntoParts(){
  var partsTab = document.getElementById('parts');
  if(!partsTab || document.getElementById('psInlineBtn')) return;
  var title = partsTab.querySelector('.panel-title');
  if(!title) return;
  var btn = document.createElement('button');
  btn.id = 'psInlineBtn';
  btn.className = 'btn';
  btn.style.cssText = 'background:linear-gradient(135deg,#f97316,#c2410c);margin-bottom:10px;';
  btn.textContent = '🔍 Search Parts (by number / description)';
  btn.onclick = psOpen;
  title.parentNode.insertBefore(btn, title.nextSibling);
}

setInterval(psInjectIntoParts, 900);
setTimeout(psInjectIntoParts, 600);
document.getElementById('psModal').addEventListener('click',function(e){if(e.target===this)psClose();});
</script>
"""
