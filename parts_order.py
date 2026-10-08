"""Parts ordering from suppliers — PO workflow + supplier management."""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _c():
    import db
    if not db.is_ready():
        raise HTTPException(503, "DB not ready")
    return db.get_client()


@router.get("/api/suppliers")
def list_suppliers():
    r = _c().table("suppliers").select("*").order("name").execute()
    return {"suppliers": r.data or []}


@router.post("/api/suppliers")
async def create_supplier(r: Request):
    d = await r.json()
    sid = str(uuid.uuid4())[:8]
    row = {
        "id": sid,
        "name": d.get("name", ""),
        "phone": d.get("phone", ""),
        "email": d.get("email", ""),
        "address": d.get("address", ""),
        "notes": d.get("notes", ""),
        "created": datetime.utcnow().isoformat(),
    }
    _c().table("suppliers").insert(row).execute()
    return {"success": True, "supplier": row}


@router.delete("/api/suppliers/{sid}")
def delete_supplier(sid: str):
    _c().table("suppliers").delete().eq("id", sid).execute()
    return {"success": True}


@router.get("/api/po/list")
def list_pos(status: str = None):
    q = _c().table("purchase_orders").select("*").order("created", desc=True)
    if status:
        q = q.eq("status", status)
    r = q.execute()
    pos = r.data or []
    for po in pos:
        items = _c().table("po_items").select("*").eq("po_id", po["id"]).execute().data or []
        po["items_detail"] = items
    return {"purchase_orders": pos}


@router.post("/api/po/create")
async def create_po(r: Request):
    d = await r.json()
    pid = str(uuid.uuid4())[:8]
    po_num = "PO-" + datetime.now().strftime("%y%m%d") + "-" + pid[:4].upper()
    total = 0
    items = d.get("items") or []
    for it in items:
        total += float(it.get("qty", 1)) * float(it.get("unit_price", 0))

    po = {
        "id": pid,
        "po_number": po_num,
        "supplier": d.get("supplier", ""),
        "supplier_phone": d.get("supplier_phone", ""),
        "supplier_email": d.get("supplier_email", ""),
        "items": "",
        "total": total,
        "status": "draft",
        "expected_date": d.get("expected_date", ""),
        "notes": d.get("notes", ""),
        "created": _now(),
    }
    _c().table("purchase_orders").insert(po).execute()

    for it in items:
        iid = str(uuid.uuid4())[:8]
        line_total = float(it.get("qty", 1)) * float(it.get("unit_price", 0))
        _c().table("po_items").insert({
            "id": iid,
            "po_id": pid,
            "part_number": it.get("part_number", ""),
            "description": it.get("description", ""),
            "qty": int(it.get("qty", 1)),
            "unit_price": float(it.get("unit_price", 0)),
            "line_total": line_total,
            "received": False,
        }).execute()

    return {"success": True, "po_id": pid, "po_number": po_num, "total": total}


@router.post("/api/po/{pid}/status")
async def update_po_status(pid: str, r: Request):
    d = await r.json()
    new_status = (d.get("status") or "").strip()
    valid = ["draft", "sent", "confirmed", "shipped", "received", "cancelled"]
    if new_status not in valid:
        raise HTTPException(400, f"Status must be one of: {valid}")
    update = {"status": new_status}
    if new_status == "received":
        update["received_at"] = datetime.utcnow().isoformat()
    _c().table("purchase_orders").update(update).eq("id", pid).execute()
    return {"success": True, "status": new_status}


@router.post("/api/po/{pid}/receive")
async def receive_po(pid: str, r: Request):
    items = _c().table("po_items").select("*").eq("po_id", pid).execute().data or []
    if not items:
        raise HTTPException(400, "No items on this PO")

    existing = _c().table("inventory").select("*").execute().data or []
    existing_by_part = {}
    for inv in existing:
        pn = (inv.get("part_number") or "").strip().upper()
        if pn:
            existing_by_part[pn] = inv

    added = 0
    updated = 0
    for it in items:
        pn = (it.get("part_number") or "").strip()
        qty = int(it.get("qty", 0))
        if not pn or qty <= 0:
            continue
        key = pn.upper()
        if key in existing_by_part:
            inv = existing_by_part[key]
            new_qty = int(inv.get("qty") or 0) + qty
            _c().table("inventory").update({"qty": new_qty}).eq("id", inv["id"]).execute()
            updated += 1
        else:
            iid = str(uuid.uuid4())[:8]
            _c().table("inventory").insert({
                "id": iid,
                "part_number": pn,
                "name": it.get("description", ""),
                "category": "",
                "qty": qty,
                "min_qty": 5,
                "cost_price": float(it.get("unit_price", 0)),
                "sell_price": float(it.get("unit_price", 0)) * 1.4,
                "supplier": "",
                "created": datetime.now().strftime("%Y-%m-%d"),
            }).execute()
            added += 1
        _c().table("po_items").update({"received": True}).eq("id", it["id"]).execute()

    _c().table("purchase_orders").update({
        "status": "received",
        "received_at": datetime.utcnow().isoformat(),
    }).eq("id", pid).execute()

    return {"success": True, "added_to_inventory": added, "updated_inventory": updated}


@router.delete("/api/po/{pid}")
def delete_po(pid: str):
    _c().table("po_items").delete().eq("po_id", pid).execute()
    _c().table("purchase_orders").delete().eq("id", pid).execute()
    return {"success": True}


PARTS_ORDER_HTML = r"""
<style>
#poModal{display:none;position:fixed;inset:0;background:#0a1018;z-index:9999;overflow:auto;}
#poInner{max-width:700px;margin:0 auto;padding:16px;color:#e6edf5;min-height:100vh;}
.poIn{width:100%;padding:12px;background:#0f1520;border:1px solid #1e2938;border-radius:9px;
color:#e6edf5;font-size:14px;box-sizing:border-box;font-family:inherit;margin-bottom:8px;}
.poBtn{width:100%;padding:14px;background:#0ea5e9;color:#fff;border:none;border-radius:10px;
font-weight:700;font-size:15px;cursor:pointer;margin-bottom:8px;}
.poBtn.dark{background:#1e2938;}
.poBtn.green{background:#10b981;}
.poBtn.red{background:#ef4444;}
.poRow{display:flex;gap:8px;}
.poRow .poIn{flex:1;}
.poCard{background:#0f1520;border:1px solid #1e2938;border-radius:10px;padding:12px;margin-bottom:8px;}
.poHeader{display:flex;justify-content:space-between;align-items:center;
padding-bottom:14px;border-bottom:2px solid #1e2938;margin-bottom:14px;}
.poBadge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;
font-weight:700;color:#fff;}
.poBadge.draft{background:#6b7280;}
.poBadge.sent{background:#f59e0b;}
.poBadge.confirmed{background:#3b82f6;}
.poBadge.shipped{background:#8b5cf6;}
.poBadge.received{background:#10b981;}
.poBadge.cancelled{background:#ef4444;}
.poLineItem{display:flex;justify-content:space-between;padding:6px 0;
border-bottom:1px solid #1e2938;font-size:13px;}
.poLineItem:last-child{border-bottom:none;}
.poTabs{display:flex;gap:4px;margin-bottom:12px;background:#0a1018;padding:4px;border-radius:10px;}
.poTab{flex:1;padding:9px;background:transparent;color:#7b8da3;border:none;
border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;}
.poTab.active{background:#0ea5e9;color:#fff;}
#poItemsList{margin-top:10px;}
.poItemEntry{background:#0a1018;border:1px solid #1e2938;border-radius:8px;padding:10px;margin-bottom:6px;}
</style>

<div id="poModal">
<div id="poInner">
<div class="poHeader">
<div>
<div style="font-size:11px;color:#7b8da3;letter-spacing:.5px;">WORKSHOP</div>
<div style="font-size:18px;font-weight:800;color:#0ea5e9;">Parts Ordering</div>
</div>
<button onclick="poClose()" style="background:#1e2938;color:#fff;border:none;
border-radius:8px;padding:8px 14px;cursor:pointer;">X</button>
</div>

<div class="poTabs">
<button class="poTab active" data-t="new" onclick="poTab('new')">New Order</button>
<button class="poTab" data-t="list" onclick="poTab('list')">Orders</button>
<button class="poTab" data-t="suppliers" onclick="poTab('suppliers')">Suppliers</button>
</div>

<div id="poNewTab">
<div class="poCard">
<h3 style="margin-bottom:10px;color:#0ea5e9;">New Purchase Order</h3>
<div class="poRow">
<input id="poSupplier" class="poIn" placeholder="Supplier name">
<button class="poBtn dark" style="width:auto;padding:12px 14px;margin:0;" onclick="poLoadSupplierList()">Pick</button>
</div>
<input id="poSupplierPhone" class="poIn" placeholder="Supplier phone">
<input id="poSupplierEmail" class="poIn" placeholder="Supplier email">
<input id="poExpected" class="poIn" type="date" placeholder="Expected delivery">
</div>

<div class="poCard">
<h3 style="margin-bottom:10px;color:#0ea5e9;">Parts to Order</h3>
<div id="poItemsList"></div>
<button class="poBtn green" onclick="poAddItem()">+ Add Line Item</button>
</div>

<div class="poCard">
<textarea id="poNotes" class="poIn" rows="2" placeholder="Notes (optional)"></textarea>
<button class="poBtn" onclick="poSubmit()">Save Draft PO</button>
</div>
</div>

<div id="poListTab" style="display:none;"></div>

<div id="poSuppliersTab" style="display:none;">
<div class="poCard">
<h3 style="margin-bottom:10px;color:#0ea5e9;">Add Supplier</h3>
<input id="supName" class="poIn" placeholder="Supplier name">
<input id="supPhone" class="poIn" placeholder="Phone">
<input id="supEmail" class="poIn" placeholder="Email">
<input id="supAddress" class="poIn" placeholder="Address">
<button class="poBtn green" onclick="poSaveSupplier()">Save Supplier</button>
</div>
<div id="poSupplierList"></div>
</div>

<div id="poRes" style="display:none;background:#0a1018;border:1px solid #1e2938;
border-radius:10px;padding:12px;margin-top:10px;font-size:13px;white-space:pre-wrap;"></div>
</div>
</div>

<script>
var _poItems = [];

function poOpen(){document.getElementById('poModal').style.display='block';poRefresh();}
function poClose(){document.getElementById('poModal').style.display='none';}
function poTab(t){
  document.querySelectorAll('.poTab').forEach(function(b){b.classList.toggle('active',b.dataset.t===t);});
  document.getElementById('poNewTab').style.display = t==='new'?'block':'none';
  document.getElementById('poListTab').style.display = t==='list'?'block':'none';
  document.getElementById('poSuppliersTab').style.display = t==='suppliers'?'block':'none';
  if(t==='list')poLoadList();
  if(t==='suppliers')poLoadSuppliers();
}
function poRes(t){var e=document.getElementById('poRes');e.textContent=t;e.style.display='block';}

async function poGet(p){var r=await fetch(p);var t=await r.text();try{return JSON.parse(t);}catch(e){return {error:t.slice(0,200)};}}
async function poPost(p,b){var r=await fetch(p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});var t=await r.text();try{return JSON.parse(t);}catch(e){return {error:t.slice(0,200)};}}
async function poDel(p){var r=await fetch(p,{method:'DELETE'});return r.json();}

function poAddItem(){
  var iid = 'it_'+Date.now()+'_'+Math.random().toString(36).slice(2,6);
  _poItems.push({id:iid,part_number:'',description:'',qty:1,unit_price:0});
  poRenderItems();
}
function poRemoveItem(iid){
  _poItems = _poItems.filter(function(x){return x.id!==iid;});
  poRenderItems();
}
function poUpdateItem(iid, field, val){
  for(var i=0;i<_poItems.length;i++){
    if(_poItems[i].id===iid){_poItems[i][field]=val;}
  }
}
function poRenderItems(){
  var h='';
  _poItems.forEach(function(it){
    h+='<div class="poItemEntry">';
    h+='<input class="poIn" placeholder="Part number" value="'+it.part_number+'" onchange="poUpdateItem(\''+it.id+'\',\'part_number\',this.value)">';
    h+='<input class="poIn" placeholder="Description" value="'+it.description+'" onchange="poUpdateItem(\''+it.id+'\',\'description\',this.value)">';
    h+='<div class="poRow">';
    h+='<input class="poIn" type="number" placeholder="Qty" value="'+it.qty+'" onchange="poUpdateItem(\''+it.id+'\',\'qty\',parseInt(this.value)||1)">';
    h+='<input class="poIn" type="number" placeholder="Unit R" value="'+it.unit_price+'" onchange="poUpdateItem(\''+it.id+'\',\'unit_price\',parseFloat(this.value)||0)">';
    h+='<button class="poBtn red" style="width:auto;padding:12px 14px;margin:0;" onclick="poRemoveItem(\''+it.id+'\')">X</button>';
    h+='</div></div>';
  });
  document.getElementById('poItemsList').innerHTML = h;
}

async function poLoadSupplierList(){
  var d = await poGet('/api/suppliers');
  var s = d.suppliers||[];
  if(!s.length){alert('No suppliers yet. Add one in the Suppliers tab.');return;}
  var names = s.map(function(x,i){return (i+1)+'. '+x.name;}).join('\n');
  var pick = prompt('Pick a supplier:\n'+names);
  var idx = parseInt(pick);
  if(idx>=1 && idx<=s.length){
    document.getElementById('poSupplier').value = s[idx-1].name;
    document.getElementById('poSupplierPhone').value = s[idx-1].phone||'';
    document.getElementById('poSupplierEmail').value = s[idx-1].email||'';
  }
}

async function poSubmit(){
  var supplier = document.getElementById('poSupplier').value.trim();
  if(!supplier){poRes('Supplier name required');return;}
  if(_poItems.length===0){poRes('Add at least one line item');return;}
  var d = await poPost('/api/po/create',{
    supplier: supplier,
    supplier_phone: document.getElementById('poSupplierPhone').value.trim(),
    supplier_email: document.getElementById('poSupplierEmail').value.trim(),
    expected_date: document.getElementById('poExpected').value,
    notes: document.getElementById('poNotes').value.trim(),
    items: _poItems
  });
  if(d.success){
    poRes('PO '+d.po_number+' created. Total: R'+d.total.toFixed(2));
    _poItems = []; poRenderItems();
    ['poSupplier','poSupplierPhone','poSupplierEmail','poExpected','poNotes'].forEach(function(i){document.getElementById(i).value='';});
    setTimeout(function(){poTab('list');},800);
  } else {
    poRes('Error: '+(d.detail||JSON.stringify(d)));
  }
}

async function poLoadList(){
  document.getElementById('poListTab').innerHTML = '<div style="text-align:center;padding:20px;color:#7b8da3;">Loading...</div>';
  var d = await poGet('/api/po/list');
  var pos = d.purchase_orders||[];
  if(!pos.length){
    document.getElementById('poListTab').innerHTML = '<div style="text-align:center;padding:40px;color:#7b8da3;">No orders yet.</div>';
    return;
  }
  var h='';
  pos.forEach(function(po){
    var st = po.status||'draft';
    h+='<div class="poCard">';
    h+='<div style="display:flex;justify-content:space-between;align-items:center;">';
    h+='<div><b style="color:#0ea5e9;">'+(po.po_number||'PO-'+po.id)+'</b> <span class="poBadge '+st+'">'+st.toUpperCase()+'</span></div>';
    h+='<div style="font-weight:700;">R'+(po.total||0).toFixed(2)+'</div>';
    h+='</div>';
    h+='<div style="font-size:13px;color:#94a3b8;margin-top:6px;">Supplier: '+(po.supplier||'-')+'</div>';
    h+='<div style="font-size:12px;color:#7b8da3;">Created: '+(po.created||'-')+'</div>';
    if(po.items_detail && po.items_detail.length){
      h+='<div style="margin-top:8px;border-top:1px solid #1e2938;padding-top:8px;">';
      po.items_detail.forEach(function(it){
        h+='<div class="poLineItem"><span>'+(it.part_number||'')+' — '+(it.description||'')+'</span><span>'+it.qty+' x R'+(it.unit_price||0).toFixed(2)+'</span></div>';
      });
      h+='</div>';
    }
    h+='<div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap;">';
    if(st==='draft'){
      h+='<button class="poBtn" style="flex:1;padding:10px;font-size:13px;" onclick="poSetStatus(\''+po.id+'\',\'sent\')">Mark Sent</button>';
    } else if(st==='sent'){
      h+='<button class="poBtn" style="flex:1;padding:10px;font-size:13px;" onclick="poSetStatus(\''+po.id+'\',\'confirmed\')">Confirmed</button>';
    } else if(st==='confirmed'){
      h+='<button class="poBtn" style="flex:1;padding:10px;font-size:13px;" onclick="poSetStatus(\''+po.id+'\',\'shipped\')">Shipped</button>';
    } else if(st==='shipped'){
      h+='<button class="poBtn green" style="flex:1;padding:10px;font-size:13px;" onclick="poReceive(\''+po.id+'\')">Receive Into Stock</button>';
    }
    h+='<button class="poBtn dark" style="flex:1;padding:10px;font-size:13px;" onclick="poWhatsApp(\''+po.id+'\')">Share</button>';
    h+='<button class="poBtn red" style="flex:1;padding:10px;font-size:13px;" onclick="poDelete(\''+po.id+'\')">Delete</button>';
    h+='</div></div>';
  });
  document.getElementById('poListTab').innerHTML = h;
}

async function poSetStatus(pid, status){
  var d = await poPost('/api/po/'+pid+'/status',{status:status});
  if(d.success){poLoadList();}else{alert('Error: '+(d.detail||''));}
}

async function poReceive(pid){
  if(!confirm('Receive this PO into inventory?'))return;
  var d = await poPost('/api/po/'+pid+'/receive',{});
  if(d.success){
    alert('Received. Added: '+d.added_to_inventory+', Updated: '+d.updated_inventory);
    poLoadList();
  } else {alert('Error: '+(d.detail||''));}
}

function poWhatsApp(pid){
  poGet('/api/po/list').then(function(d){
    var po = (d.purchase_orders||[]).find(function(x){return x.id===pid;});
    if(!po)return;
    var txt = '*Purchase Order '+(po.po_number||po.id)+'*\n\nSupplier: '+(po.supplier||'')+'\n\n';
    (po.items_detail||[]).forEach(function(it){
      txt += '• '+(it.part_number||'')+' — '+(it.description||'')+' — '+it.qty+' x R'+it.unit_price+'\n';
    });
    txt += '\nTotal: R'+(po.total||0).toFixed(2);
    var phone = (po.supplier_phone||'').replace(/\D/g,'');
    window.open(phone?'https://wa.me/'+phone+'?text='+encodeURIComponent(txt):'https://wa.me/?text='+encodeURIComponent(txt),'_blank');
  });
}

async function poDelete(pid){
  if(!confirm('Delete this PO?'))return;
  await poDel('/api/po/'+pid);
  poLoadList();
}

async function poLoadSuppliers(){
  document.getElementById('poSupplierList').innerHTML = '<div style="text-align:center;padding:20px;color:#7b8da3;">Loading...</div>';
  var d = await poGet('/api/suppliers');
  var sups = d.suppliers||[];
  if(!sups.length){
    document.getElementById('poSupplierList').innerHTML = '<div style="text-align:center;padding:20px;color:#7b8da3;">No suppliers yet.</div>';
    return;
  }
  var h='';
  sups.forEach(function(s){
    h+='<div class="poCard">';
    h+='<div style="font-weight:700;color:#0ea5e9;">'+s.name+'</div>';
    if(s.phone)h+='<div style="font-size:13px;">'+s.phone+'</div>';
    if(s.email)h+='<div style="font-size:12px;color:#94a3b8;">'+s.email+'</div>';
    h+='<button class="poBtn red" style="margin-top:8px;padding:8px;font-size:12px;" onclick="poDeleteSupplier(\''+s.id+'\')">Delete</button>';
    h+='</div>';
  });
  document.getElementById('poSupplierList').innerHTML = h;
}

async function poSaveSupplier(){
  var n = document.getElementById('supName').value.trim();
  if(!n){alert('Name required');return;}
  var d = await poPost('/api/suppliers',{
    name:n,
    phone:document.getElementById('supPhone').value.trim(),
    email:document.getElementById('supEmail').value.trim(),
    address:document.getElementById('supAddress').value.trim()
  });
  if(d.success){
    ['supName','supPhone','supEmail','supAddress'].forEach(function(i){document.getElementById(i).value='';});
    poLoadSuppliers();
  }
}

async function poDeleteSupplier(sid){
  if(!confirm('Delete?'))return;
  await poDel('/api/suppliers/'+sid);
  poLoadSuppliers();
}

function poRefresh(){
  poRenderItems();
}

function poInjectIntoPurchase(){
  var poTab = document.getElementById('purchase');
  if(!poTab || document.getElementById('poInlineBtn')) return;
  var title = poTab.querySelector('.panel-title');
  if(!title) return;
  var btn = document.createElement('button');
  btn.id = 'poInlineBtn';
  btn.className = 'btn';
  btn.style.cssText = 'background:linear-gradient(135deg,#0ea5e9,#0369a1);margin-bottom:10px;';
  btn.textContent = '📦 New Purchase Order (with Suppliers)';
  btn.onclick = poOpen;
  title.parentNode.insertBefore(btn, title.nextSibling);
}

setInterval(poInjectIntoPurchase, 900);
setTimeout(poInjectIntoPurchase, 600);
document.getElementById('poModal').addEventListener('click',function(e){
  if(e.target===this)poClose();
});
</script>
"""
