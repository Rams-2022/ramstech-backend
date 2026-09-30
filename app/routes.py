# app/routes.py — All API endpoints
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
import openai, uuid, csv, io, json
from app.config import OPENAI_KEY, MAX_IMAGE_SIZE
from app.database import (list_all, get_one, save_one, delete_one,
                          get_workshop, save_workshop, now, today)
from app import data as D

router = APIRouter()

# ═══ HEALTH ═══
@router.get("/health")
def health():
    from app.database import DB_READY
    return {"status":"healthy","database":"supabase" if DB_READY else "memory"}

# ═══ REFERENCE ═══
@router.get("/api/fault-codes")
def codes(search: str = None):
    r = list(D.FAULT_CODES.values())
    if search:
        q = search.lower()
        r = [c for c in r if q in c["code"].lower() or q in c["description"].lower()]
    return {"codes": r}

@router.get("/api/specs")
def specs(): return {"specs": D.VEHICLE_SPECS}

@router.get("/api/intervals")
def intervals(): return {"intervals": D.INTERVALS}

@router.get("/api/book-times")
def book_times(): return {"times": D.BOOK_TIMES}

@router.get("/api/torque")
def torque(): return {"bolts": D.TORQUE, "sequences": D.SEQ}

@router.get("/api/bulbs")
def bulbs(): return {"bulbs": D.BULBS}

@router.get("/api/batteries")
def batteries(): return {"batteries": D.BATTERIES}

@router.get("/api/tyres")
def tyres(): return {"tyres": D.TYRES}

@router.get("/api/wiring")
def wiring(): return {"circuits": D.WIRING}

@router.get("/api/obd-pids")
def obd_pids(): return {"pids": D.PIDS}

@router.get("/api/vin/{vin}")
def decode_vin(vin: str):
    v = vin.strip().upper()
    if len(v) != 17: raise HTTPException(400, "VIN must be exactly 17 characters")
    mfr, country = D.WMI_DB.get(v[:3], ("Unknown","Unknown"))
    plants = {"A":"Ingolstadt","B":"Brussels","D":"Dingolfing","F":"Flint","H":"Hiroshima","T":"Toyota City","U":"Ulsan","W":"Wolfsburg","Y":"Yokohama"}
    return {"vin":v,"manufacturer":mfr,"country":country,"year":D.YEAR_CODES.get(v[9],"Unknown"),"plant":plants.get(v[10],"Unknown"),"serial":v[11:]}

@router.post("/api/bolt-calc")
async def bolt_calc(r: Request):
    d = await r.json(); size = d.get("size","M8"); grade = d.get("grade","8.8"); cond = d.get("condition","dry")
    tm = {"8.8":800,"10.9":1040,"12.9":1220}; am = {"M6":20.1,"M8":36.6,"M10":58.0,"M12":84.3,"M14":115.0,"M16":157.0,"M20":245.0}; km = {"dry":0.20,"oiled":0.17,"moly":0.14}
    ts = tm.get(grade,800); a = am.get(size,36.6); k = km.get(cond,0.20)
    cf = 0.75*ts*a; dm = float(size.replace("M",""))/1000.0; nm = k*dm*cf
    return {"size":size,"grade":grade,"condition":cond,"nm":nm,"ftlb":nm*0.73756,"clamp_kn":cf/1000}

# ═══ AI ═══
@router.post("/api/chat")
async def chat(r: Request):
    d = await r.json(); msg = d.get("message","")
    if not msg: raise HTTPException(400,"Message required")
    if not OPENAI_KEY: return {"reply":"AI not configured"}
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        resp = c.chat.completions.create(model="gpt-3.5-turbo",
            messages=[{"role":"system","content":"You are RamsTech AI, expert mechanic."},{"role":"user","content":msg}],
            max_tokens=800, temperature=0.3)
        return {"reply": resp.choices[0].message.content}
    except Exception as e: return {"reply": f"Error: {str(e)}"}

@router.post("/api/diagnose/photo")
async def diagnose_photo(r: Request):
    d = await r.json(); img = d.get("image_base64",""); veh = d.get("vehicle_info","")
    if not img: raise HTTPException(400,"Image required")
    if not OPENAI_KEY: return {"success":False,"error":"AI not configured"}
    if img.startswith("data:"): img = img.split(",",1)[1]
    if len(img) > MAX_IMAGE_SIZE: return {"success":False,"error":"Image too large"}
    p = f"""Expert mechanic. Vehicle: {veh or 'N/A'}
Respond ONLY JSON: {{"problem":"S","description":"D","confidence":"High|Medium|Low","possible_causes":["C"],"diagnostic_steps":["S"],"safety_warnings":["W"]}}"""
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        resp = c.chat.completions.create(model="gpt-4o", messages=[{"role":"user","content":[{"type":"text","text":p},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}], max_tokens=2000, temperature=0.2, response_format={"type":"json_object"})
        parsed = json.loads(resp.choices[0].message.content); parsed["success"]=True; return parsed
    except Exception as e: return {"success":False,"error":str(e)}

@router.post("/api/paint/match")
async def match_paint(r: Request):
    d = await r.json(); img = d.get("image_base64",""); veh = d.get("vehicle_info","")
    if not img: raise HTTPException(400,"Image required")
    if not OPENAI_KEY: return {"success":False,"error":"AI not configured"}
    if img.startswith("data:"): img = img.split(",",1)[1]
    if len(img) > MAX_IMAGE_SIZE: return {"success":False,"error":"Image too large"}
    p = f"""Expert paint tech. Vehicle: {veh or 'N/A'}
Respond ONLY JSON: {{"detected_colour":{{"name":"N","hex_code":"#RRGGBB","finish":"Solid|Metallic|Pearl","colour_family":"White|Black|Red|Blue|Silver|Grey"}},"confidence":"High|Medium|Low","brand_codes":[{{"brand":"DuPont","code":"C"}}],"safety_warnings":["W"]}}"""
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        resp = c.chat.completions.create(model="gpt-4o", messages=[{"role":"user","content":[{"type":"text","text":p},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}], max_tokens=2000, temperature=0.2, response_format={"type":"json_object"})
        parsed = json.loads(resp.choices[0].message.content); parsed["success"]=True; return parsed
    except Exception as e: return {"success":False,"error":str(e)}

# ═══ STATS ═══
@router.get("/api/stats")
def stats():
    jobs = list_all("jobs"); invs = list_all("invoices"); custs = list_all("customers"); exps = list_all("expenses")
    total = len(jobs); done = sum(1 for j in jobs if j.get("status")=="Completed")
    open_j = sum(1 for j in jobs if j.get("status")!="Completed")
    new_j = sum(1 for j in jobs if j.get("status")=="New")
    prog = sum(1 for j in jobs if j.get("status")=="In Progress")
    rev = sum(float(i.get("total",0)) for i in invs); exp = sum(float(e.get("amount",0)) for e in exps)
    labels,data = [],[]
    for i in range(6,-1,-1):
        day = (datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(day[5:]); data.append(round(sum(float(x.get("total",0)) for x in invs if (x.get("created") or "").startswith(day)),2))
    return {"jobs_total":total,"jobs_open":open_j,"jobs_completed":done,"jobs_new":new_j,"jobs_progress":prog,"customers":len(custs),"revenue":round(rev,2),"expenses":round(exp,2),"revenue_labels":labels,"revenue_data":data}

@router.get("/api/analytics")
def analytics():
    jobs = list_all("jobs"); invs = list_all("invoices")
    total_rev = sum(float(i.get("total",0)) for i in invs)
    avg_inv = total_rev/len(invs) if invs else 0
    svc = {}
    for j in jobs:
        c = (j.get("complaint") or "").strip()[:30]
        if c: svc[c] = svc.get(c,0)+1
    top_services = [{"name":k,"count":v} for k,v in sorted(svc.items(), key=lambda x:-x[1])[:5]]
    cr = {}
    for i in invs:
        n = i.get("customer","")
        if n: cr[n] = cr.get(n,0)+float(i.get("total",0))
    top_customers = [{"name":k,"total":v} for k,v in sorted(cr.items(), key=lambda x:-x[1])[:5]]
    return {"total_revenue":total_rev,"avg_invoice":avg_inv,"invoices_count":len(invs),"jobs_count":len(jobs),"top_services":top_services,"top_customers":top_customers}

@router.get("/api/warranty")
def warranty_list():
    items = []
    for j in list_all("jobs"):
        if j.get("status")=="Completed" and int(j.get("warranty_months",0) or 0)>0:
            try:
                done = datetime.strptime((j.get("created") or "")[:10],"%Y-%m-%d"); months = int(j["warranty_months"])
                year = done.year + (done.month+months-1)//12; month = ((done.month+months-1)%12)+1
                expiry = done.replace(year=year,month=month); days_left = (expiry-datetime.now()).days
                items.append({"id":j["id"],"customer":j.get("customer",""),"vehicle":j.get("vehicle",""),"expiry":expiry.strftime("%Y-%m-%d"),"days_left":days_left,"status":"active" if days_left>0 else "expired"})
            except Exception: pass
    items.sort(key=lambda x:x["days_left"]); return {"warranties":items}

@router.get("/api/export/tax")
def export_tax(from_date: str = None, to_date: str = None):
    o = io.StringIO(); w = csv.writer(o)
    w.writerow(["Date","Type","Description","Customer/Note","Amount","VAT"])
    for i in list_all("invoices"):
        d = (i.get("created") or "")[:10]
        if from_date and d < from_date: continue
        if to_date and d > to_date: continue
        w.writerow([d,"INCOME",i.get("description",""),i.get("customer",""),f"{float(i.get('total',0)):.2f}",f"{float(i.get('vat',0)):.2f}"])
    for e in list_all("expenses"):
        d = e.get("date","")
        if from_date and d < from_date: continue
        if to_date and d > to_date: continue
        w.writerow([d,"EXPENSE",e.get("category",""),e.get("note",""),f"-{float(e.get('amount',0)):.2f}","0.00"])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=tax_report.csv"})

# ═══ JOBS ═══
@router.get("/api/jobs")
def list_jobs(): return {"jobs": list_all("jobs")}

@router.post("/api/jobs")
async def create_job(r: Request):
    d = await r.json(); jid = str(uuid.uuid4())[:6]
    row = {"id":jid,"customer":d.get("customer",""),"phone":d.get("phone",""),"vehicle":d.get("vehicle",""),"registration":d.get("registration",""),"complaint":d.get("complaint",""),"assigned_to":d.get("assigned_to",""),"warranty_months":int(d.get("warranty_months",6)),"photos_before":d.get("photos_before",[]),"photos_after":[],"signature":"","status":"New","created":now()}
    save_one("jobs", jid, row); return {"success":True,"job":row}

@router.put("/api/jobs/{jid}")
async def update_job(jid: str, r: Request):
    d = await r.json(); job = get_one("jobs", jid)
    if job:
        job["status"] = d.get("status", job["status"])
        save_one("jobs", jid, job)
    return {"success":True}

@router.delete("/api/jobs/{jid}")
def delete_job(jid: str): delete_one("jobs",jid); return {"success":True}

# ═══ CUSTOMERS ═══
@router.get("/api/customers")
def list_cust(): return {"customers": list_all("customers")}

@router.post("/api/customers")
async def create_cust(r: Request):
    d = await r.json(); cid = str(uuid.uuid4())[:6]
    row = {"id":cid,"name":d.get("name",""),"phone":d.get("phone",""),"email":d.get("email",""),"created":today()}
    save_one("customers",cid,row); return {"success":True,"customer":row}

@router.delete("/api/customers/{cid}")
def delete_cust(cid: str): delete_one("customers",cid); return {"success":True}

# ═══ INVOICES ═══
@router.get("/api/invoices")
def list_inv(): return {"invoices": list_all("invoices")}

@router.post("/api/invoices")
async def create_inv(r: Request):
    d = await r.json(); labour = float(d.get("labour",0)); parts = float(d.get("parts",0))
    subtotal = labour+parts; vat = subtotal*0.15; total = subtotal+vat
    iid = str(uuid.uuid4())[:6]
    row = {"id":iid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),"description":d.get("description",""),"labour":labour,"parts":parts,"subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    save_one("invoices",iid,row); return {"success":True,"invoice":row}

@router.delete("/api/invoices/{iid}")
def delete_inv(iid: str): delete_one("invoices",iid); return {"success":True}

# ═══ QUOTES ═══
@router.get("/api/quotes")
def list_quotes(): return {"quotes": list_all("quotes")}

@router.post("/api/quotes")
async def create_quote(r: Request):
    d = await r.json(); labour = float(d.get("labour",0)); parts = float(d.get("parts",0))
    subtotal = labour+parts; vat = subtotal*0.15; total = subtotal+vat
    qid = str(uuid.uuid4())[:6]
    row = {"id":qid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),"description":d.get("description",""),"labour":labour,"parts":parts,"subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    save_one("quotes",qid,row); return {"success":True,"quote":row}

@router.post("/api/quotes/{qid}/accept")
async def accept_quote(qid: str):
    q = get_one("quotes",qid)
    if not q: raise HTTPException(404,"Not found")
    iid = str(uuid.uuid4())[:6]
    inv = {"id":iid,"customer":q["customer"],"vehicle":q["vehicle"],"description":q["description"],"labour":q["labour"],"parts":q["parts"],"subtotal":q["subtotal"],"vat":q["vat"],"total":q["total"],"created":now()}
    save_one("invoices",iid,inv); delete_one("quotes",qid); return {"success":True,"invoice":inv}

@router.delete("/api/quotes/{qid}")
def delete_quote(qid: str): delete_one("quotes",qid); return {"success":True}

# ═══ APPOINTMENTS ═══
@router.get("/api/appointments")
def list_appts(): return {"appointments": list_all("appointments")}

@router.post("/api/appointments")
async def create_appt(r: Request):
    d = await r.json(); aid = str(uuid.uuid4())[:6]
    row = {"id":aid,"customer":d.get("customer",""),"phone":d.get("phone",""),"vehicle":d.get("vehicle",""),"service":d.get("service",""),"date":d.get("date",""),"time":d.get("time",""),"created":now()}
    save_one("appointments",aid,row); return {"success":True,"appointment":row}

@router.delete("/api/appointments/{aid}")
def delete_appt(aid: str): delete_one("appointments",aid); return {"success":True}

# ═══ INVENTORY ═══
@router.get("/api/inventory")
def list_inv_items(): return {"items": list_all("inventory")}

@router.get("/api/inventory/low-stock")
def low_stock(): return {"items":[{"id":i["id"],"name":i["name"],"qty":int(i.get("qty",0)),"min":int(i.get("min_qty",5))} for i in list_all("inventory") if int(i.get("qty",0))<=int(i.get("min_qty",5))]}

@router.post("/api/inventory")
async def add_inv_item(r: Request):
    d = await r.json(); iid = str(uuid.uuid4())[:6]
    row = {"id":iid,"part_number":d.get("part_number",""),"name":d.get("name",""),"category":d.get("category",""),"qty":int(d.get("qty",0)),"min_qty":int(d.get("min_qty",5)),"cost_price":float(d.get("cost_price",0)),"sell_price":float(d.get("sell_price",0)),"supplier":d.get("supplier",""),"created":today()}
    save_one("inventory",iid,row); return {"success":True,"item":row}

@router.post("/api/inventory/{iid}/adjust")
async def adjust_inv(iid: str, r: Request):
    d = await r.json(); item = get_one("inventory",iid)
    if not item: raise HTTPException(404,"Not found")
    item["qty"] = max(0, int(item.get("qty",0))+int(d.get("delta",0)))
    save_one("inventory",iid,item); return {"success":True,"item":item}

@router.delete("/api/inventory/{iid}")
def delete_inv_item(iid: str): delete_one("inventory",iid); return {"success":True}

# ═══ STAFF ═══
@router.get("/api/staff")
def list_staff(): return {"staff": list_all("staff")}

@router.post("/api/staff")
async def add_staff(r: Request):
    d = await r.json(); sid = str(uuid.uuid4())[:6]
    row = {"id":sid,"name":d.get("name",""),"role":d.get("role",""),"phone":d.get("phone",""),"email":d.get("email",""),"hourly_rate":float(d.get("hourly_rate",150)),"created":today()}
    save_one("staff",sid,row); return {"success":True,"staff":row}

@router.delete("/api/staff/{sid}")
def delete_staff(sid: str): delete_one("staff",sid); return {"success":True}

# ═══ EXPENSES ═══
@router.get("/api/expenses")
def list_exp(): return {"expenses": list_all("expenses")}

@router.post("/api/expenses")
async def add_exp(r: Request):
    d = await r.json(); eid = str(uuid.uuid4())[:6]
    row = {"id":eid,"category":d.get("category","Other"),"amount":float(d.get("amount",0)),"date":d.get("date",today()),"note":d.get("note",""),"created":now()}
    save_one("expenses",eid,row); return {"success":True,"expense":row}

@router.delete("/api/expenses/{eid}")
def delete_exp(eid: str): delete_one("expenses",eid); return {"success":True}

# ═══ SUPPLIERS ═══
@router.get("/api/suppliers")
def list_suppliers(): return {"suppliers": list_all("suppliers")}

@router.post("/api/suppliers")
async def add_supplier(r: Request):
    d = await r.json(); sid = str(uuid.uuid4())[:6]
    row = {"id":sid,"name":d.get("name",""),"phone":d.get("phone",""),"email":d.get("email",""),"whatsapp":d.get("whatsapp",""),"category":d.get("category",""),"account_number":d.get("account_number",""),"notes":d.get("notes",""),"created":today()}
    save_one("suppliers",sid,row); return {"success":True,"supplier":row}

@router.delete("/api/suppliers/{sid}")
def delete_supplier(sid: str): delete_one("suppliers",sid); return {"success":True}

# ═══ WORKSHOP ═══
@router.get("/api/workshop")
def get_ws(): return get_workshop()

@router.post("/api/workshop")
async def save_ws(r: Request):
    d = await r.json(); save_workshop(d); return {"success":True,"workshop":get_workshop()}
