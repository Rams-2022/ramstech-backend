from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from datetime import datetime, timedelta
import openai, os, json, uuid, csv, io

from data import (FAULT_CODES, WMI_DB, YEAR_CODES, TORQUE_SPECS, TORQUE_SEQUENCES,
                  PARTS_CATALOG, COMMON_PROBLEMS, WIRING_LIBRARY, OBD_PIDS,
                  BULB_CHART, BATTERY_SIZES, TYRE_SIZES, FUSE_BOXES,
                  INSPECTION_CATEGORIES, SERVICE_INTERVALS)
from pages import HTML_PAGE

app = FastAPI(title="RamsTech")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

# ═══════════════════════════════════
# IN-MEMORY STORES
# ═══════════════════════════════════
JOBS, CUSTOMERS, APPOINTMENTS, INVOICES, STAFF, INVENTORY = {}, {}, {}, {}, {}, {}
QUOTES, EXPENSES, CLOCKINS, PURCHASE_ORDERS = {}, {}, {}, {}
WORKSHOP = {"name":"My Workshop","phone":"","address":"","email":"","logo":"🔧","labour_rate":450}

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M")
def today(): return datetime.now().strftime("%Y-%m-%d")

# ═══════════════════════════════════
# HTML
# ═══════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def home(): return HTML_PAGE

@app.get("/health")
def health(): return {"status":"healthy","time":datetime.now().isoformat()}

# STATS
@app.get("/api/stats")
def get_stats():
    total=len(JOBS)
    open_j=sum(1 for j in JOBS.values() if j["status"]!="Completed")
    done=sum(1 for j in JOBS.values() if j["status"]=="Completed")
    new=sum(1 for j in JOBS.values() if j["status"]=="New")
    prog=sum(1 for j in JOBS.values() if j["status"]=="In Progress")
    rev=sum(i["total"] for i in INVOICES.values())
    exp=sum(e["amount"] for e in EXPENSES.values())
    labels,data=[],[]
    for i in range(6,-1,-1):
        day=(datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(day[5:])
        data.append(round(sum(inv["total"] for inv in INVOICES.values() if inv.get("created","").startswith(day)),2))
    return {"jobs_total":total,"jobs_open":open_j,"jobs_completed":done,"jobs_new":new,"jobs_progress":prog,
            "customers":len(CUSTOMERS),"revenue":round(rev,2),"expenses":round(exp,2),
            "revenue_labels":labels,"revenue_data":data}

@app.get("/api/analytics")
def get_analytics():
    tr=sum(i["total"] for i in INVOICES.values())
    te=sum(e["amount"] for e in EXPENSES.values())
    avg=tr/len(INVOICES) if INVOICES else 0
    services={}
    for j in JOBS.values():
        c=j.get("complaint","").strip()[:30]
        if c: services[c]=services.get(c,0)+1
    top_services=[{"name":k,"count":v} for k,v in sorted(services.items(),key=lambda x:-x[1])[:5]]
    cr={}
    for i in INVOICES.values():
        n=i.get("customer","")
        if n:
            if n not in cr: cr[n]={"total":0}
            cr[n]["total"]+=i["total"]
    top_customers=[{"name":k,"total":v["total"]} for k,v in sorted(cr.items(),key=lambda x:-x[1]["total"])[:5]]
    return {"total_revenue":tr,"total_expenses":te,"net_profit":tr-te,"avg_invoice":avg,
            "top_services":top_services,"top_customers":top_customers}

# WORKSHOP
@app.get("/api/workshop")
def get_workshop(): return WORKSHOP

@app.post("/api/workshop")
async def save_workshop(r: Request):
    d=await r.json(); WORKSHOP.update(d); return {"success":True,"workshop":WORKSHOP}

# STATIC DATA
@app.get("/api/fault-codes")
def list_codes(search: str = None):
    res=list(FAULT_CODES.values())
    if search:
        q=search.lower(); res=[c for c in res if q in c["code"].lower() or q in c["description"].lower()]
    return {"count":len(res),"codes":res}

@app.get("/api/problems")
def list_problems(): return {"problems":COMMON_PROBLEMS}

@app.get("/api/wiring")
def list_wiring(): return {"circuits":WIRING_LIBRARY}

@app.get("/api/obd-pids")
def list_obd(): return {"pids":OBD_PIDS}

@app.get("/api/bulbs")
def list_bulbs(): return {"bulbs":BULB_CHART}

@app.get("/api/batteries")
def list_batteries(): return {"batteries":BATTERY_SIZES}

@app.get("/api/tyres")
def list_tyres(): return {"tyres":TYRE_SIZES}

@app.get("/api/fuses")
def list_fuses(): return {"fuses":FUSE_BOXES}

@app.get("/api/parts")
def list_parts(): return {"parts":PARTS_CATALOG}

@app.get("/api/torque")
def get_torque(): return {"bolts":TORQUE_SPECS,"sequences":TORQUE_SEQUENCES}

@app.get("/api/checklists/{ctype}")
def get_checklist(ctype: str):
    c=INSPECTION_CATEGORIES.get(ctype)
    if not c: raise HTTPException(404,"Not found")
    return {"name":c["name"],"items":c["items"]}

@app.post("/api/service-calc")
async def service_calc(r: Request):
    d=await r.json()
    km=int(d.get("current_km",0))
    vt=d.get("vehicle_type","petrol")
    cfg=SERVICE_INTERVALS.get(vt,SERVICE_INTERVALS["petrol"])
    next_km=((km // cfg["km"]) + 1) * cfg["km"]
    return {"next_service_km":next_km,"months_interval":cfg["months"],"items":cfg["items"]}

@app.post("/api/bolt-calc")
async def bolt_calc(r: Request):
    d=await r.json()
    size=d.get("size","M8"); grade=d.get("grade","8.8"); cond=d.get("condition","dry")
    tm={"8.8":800,"10.9":1040,"12.9":1220}
    am={"M6":20.1,"M8":36.6,"M10":58.0,"M12":84.3,"M14":115.0,"M16":157.0,"M18":192.0,"M20":245.0}
    km={"dry":0.20,"oiled":0.17,"moly":0.14}
    ts=tm.get(grade,800); a=am.get(size,36.6); k=km.get(cond,0.20)
    cf=0.75*ts*a; dm=float(size.replace("M",""))/1000.0
    nm=k*dm*cf
    return {"size":size,"grade":grade,"condition":cond,"nm":nm,"ftlb":nm*0.73756,"clamp_kn":cf/1000}

# VIN
@app.get("/api/vin/{vin}")
def decode_vin(vin: str):
    v=vin.strip().upper()
    if len(v)!=17: raise HTTPException(400,"VIN must be 17 characters")
    m,c=WMI_DB.get(v[:3],("Unknown","Unknown"))
    return {"vin":v,"manufacturer":m,"country":c,"year":YEAR_CODES.get(v[9],"Unknown")}

# AI CHAT
@app.post("/api/chat")
async def chat(r: Request):
    d=await r.json(); msg=d.get("message","")
    if not msg: raise HTTPException(400,"Message required")
    if not OPENAI_KEY: return {"reply":"AI not configured"}
    try:
        c=openai.OpenAI(api_key=OPENAI_KEY)
        resp=c.chat.completions.create(model="gpt-3.5-turbo",
            messages=[{"role":"system","content":"You are RamsTech AI, an expert mechanic."},
                      {"role":"user","content":msg}],max_tokens=800,temperature=0.3)
        return {"reply":resp.choices[0].message.content}
    except Exception as e: return {"reply":f"Error: {str(e)}"}

# PAINT
@app.post("/api/paint/match")
async def match_paint(r: Request):
    d=await r.json(); img=d.get("image_base64",""); veh=d.get("vehicle_info","")
    if not img: raise HTTPException(400,"Image required")
    if not OPENAI_KEY: return {"success":False,"error":"AI not configured"}
    if img.startswith("data:"): img=img.split(",",1)[1]
    if len(img)>7000000: return {"success":False,"error":"Image too large"}
    prompt=f"""Expert paint tech. Vehicle: {veh or 'N/A'}
Respond ONLY valid JSON:
{{"detected_colour":{{"name":"N","hex_code":"#RRGGBB","rgb":[R,G,B],"finish":"Solid|Metallic|Pearl","colour_family":"White|Black|Red|Blue|Silver|Grey"}},"confidence":"High|Medium|Low","brand_codes":[{{"brand":"DuPont","code":"C","name":"F"}},{{"brand":"PPG","code":"C","name":"F"}}],"mixing_formula":{{"base_colour":"D","toners":[{{"name":"T","parts":"X"}}],"reducer":"R"}},"safety_warnings":["W"]}}"""
    try:
        c=openai.OpenAI(api_key=OPENAI_KEY,timeout=60.0)
        resp=c.chat.completions.create(model="gpt-4o",
            messages=[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}],
            max_tokens=2000,temperature=0.2,response_format={"type":"json_object"})
        p=json.loads(resp.choices[0].message.content); p["success"]=True; return p
    except Exception as e: return {"success":False,"error":str(e)}

@app.post("/api/diagnose/photo")
async def diagnose_photo(r: Request):
    d=await r.json(); img=d.get("image_base64",""); veh=d.get("vehicle_info","")
    if not img: raise HTTPException(400,"Image required")
    if not OPENAI_KEY: return {"success":False,"error":"AI not configured"}
    if img.startswith("data:"): img=img.split(",",1)[1]
    if len(img)>7000000: return {"success":False,"error":"Image too large"}
    prompt=f"""Expert mechanic. Vehicle: {veh or 'N/A'}
Respond ONLY valid JSON:
{{"problem":"S","description":"D","confidence":"High|Medium|Low","possible_causes":["C"],"diagnostic_steps":["S"],"safety_warnings":["W"]}}"""
    try:
        c=openai.OpenAI(api_key=OPENAI_KEY,timeout=60.0)
        resp=c.chat.completions.create(model="gpt-4o",
            messages=[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}],
            max_tokens=2000,temperature=0.2,response_format={"type":"json_object"})
        p=json.loads(resp.choices[0].message.content); p["success"]=True; return p
    except Exception as e: return {"success":False,"error":str(e)}

# JOBS
@app.get("/api/jobs")
def list_jobs(): return {"jobs":list(JOBS.values())}

@app.post("/api/jobs")
async def create_job(r: Request):
    d=await r.json()
    jid=str(len(JOBS)+1).zfill(4)
    JOBS[jid]={"id":jid,"customer":d.get("customer",""),"phone":d.get("phone",""),
               "vehicle":d.get("vehicle",""),"registration":d.get("registration",""),
               "km":int(d.get("km",0)),"complaint":d.get("complaint",""),
               "assigned_to":d.get("assigned_to",""),"photos":d.get("photos",[])[:5],
               "warranty_months":int(d.get("warranty_months",6)),
               "status":"New","timeline":[now()+" — Job created"],
               "labour_hours":0,"labour_rate":WORKSHOP.get("labour_rate",450),"parts_cost":0,
               "labour_cost":0,"subtotal":0,"vat":0,"total":0,
               "created":now()}
    return {"success":True,"job":JOBS[jid]}

@app.put("/api/jobs/{jid}")
async def update_job(jid: str, r: Request):
    d=await r.json()
    if jid not in JOBS: raise HTTPException(404,"Not found")
    if "status" in d: JOBS[jid]["status"]=d["status"]
    if "note" in d: JOBS[jid].setdefault("timeline",[]).append(now()+" — "+d["note"])
    return {"success":True,"job":JOBS[jid]}

@app.post("/api/jobs/{jid}/cost")
async def set_cost(jid: str, r: Request):
    d=await r.json()
    if jid not in JOBS: raise HTTPException(404,"Not found")
    h=float(d.get("labour_hours",0)); rate=float(d.get("labour_rate",450))
    parts=float(d.get("parts_cost",0))
    labour=h*rate; subtotal=labour+parts; vat=subtotal*0.15; total=subtotal+vat
    JOBS[jid].update({"labour_hours":h,"labour_rate":rate,"parts_cost":parts,
                      "labour_cost":labour,"subtotal":subtotal,"vat":vat,"total":total})
    JOBS[jid].setdefault("timeline",[]).append(now()+f" — Cost: R{total:.2f}")
    return {"success":True,"job":JOBS[jid]}

# CUSTOMERS
@app.get("/api/customers")
def list_customers(): return {"customers":list(CUSTOMERS.values())}

@app.post("/api/customers")
async def create_customer(r: Request):
    d=await r.json()
    cid=str(uuid.uuid4())[:8]
    CUSTOMERS[cid]={"id":cid,"name":d.get("name",""),"phone":d.get("phone",""),
                    "email":d.get("email",""),"address":d.get("address",""),
                    "created":today()}
    return {"success":True,"customer":CUSTOMERS[cid]}

# APPOINTMENTS
@app.get("/api/appointments")
def list_appts(): return {"appointments":list(APPOINTMENTS.values())}

@app.post("/api/appointments")
async def create_appt(r: Request):
    d=await r.json()
    aid=str(uuid.uuid4())[:8]
    APPOINTMENTS[aid]={"id":aid,**{k:d.get(k,"") for k in ["customer","phone","vehicle","service","date","time"]}}
    return {"success":True,"appointment":APPOINTMENTS[aid]}

@app.delete("/api/appointments/{aid}")
def delete_appt(aid: str):
    if aid not in APPOINTMENTS: raise HTTPException(404)
    del APPOINTMENTS[aid]; return {"success":True}

# QUOTES
@app.get("/api/quotes")
def list_quotes(): return {"quotes":list(QUOTES.values())}

@app.post("/api/quotes")
async def create_quote(r: Request):
    d=await r.json()
    qid=str(len(QUOTES)+1).zfill(4)
    labour=float(d.get("labour",0)); parts=float(d.get("parts",0))
    subtotal=labour+parts; vat=subtotal*0.15; total=subtotal+vat
    QUOTES[qid]={"id":qid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),
                 "description":d.get("description",""),"labour":labour,"parts":parts,
                 "subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    return {"success":True,"quote":QUOTES[qid]}

@app.post("/api/quotes/{qid}/accept")
async def accept_quote(qid: str):
    if qid not in QUOTES: raise HTTPException(404)
    q=QUOTES[qid]
    iid=str(len(INVOICES)+1).zfill(4)
    INVOICES[iid]={"id":iid,"customer":q["customer"],"vehicle":q["vehicle"],
                   "description":q["description"],"labour":q["labour"],"parts":q["parts"],
                   "subtotal":q["subtotal"],"vat":q["vat"],"total":q["total"],
                   "amount_paid":0,"paid":False,"created":now()}
    del QUOTES[qid]
    return {"success":True,"invoice":INVOICES[iid]}

@app.delete("/api/quotes/{qid}")
def delete_quote(qid: str):
    if qid not in QUOTES: raise HTTPException(404)
    del QUOTES[qid]; return {"success":True}

# INVOICES
@app.get("/api/invoices")
def list_invoices(): return {"invoices":list(INVOICES.values())}

@app.post("/api/invoices")
async def create_invoice(r: Request):
    d=await r.json()
    labour=float(d.get("labour",0)); parts=float(d.get("parts",0))
    subtotal=labour+parts; vat=subtotal*0.15; total=subtotal+vat
    iid=str(len(INVOICES)+1).zfill(4)
    INVOICES[iid]={"id":iid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),
                   "description":d.get("description",""),"labour":labour,"parts":parts,
                   "subtotal":subtotal,"vat":vat,"total":total,
                   "amount_paid":0,"paid":False,"created":now()}
    return {"success":True,"invoice":INVOICES[iid]}

@app.post("/api/invoices/{iid}/pay")
async def record_payment(iid: str, r: Request):
    d=await r.json()
    if iid not in INVOICES: raise HTTPException(404)
    amt=float(d.get("amount",0))
    INVOICES[iid]["amount_paid"]=INVOICES[iid].get("amount_paid",0)+amt
    INVOICES[iid]["paid"]=INVOICES[iid]["amount_paid"]>=INVOICES[iid]["total"]
    return {"success":True,"invoice":INVOICES[iid]}

# INVENTORY
@app.get("/api/inventory")
def list_inv(): return {"items":list(INVENTORY.values())}

@app.get("/api/inventory/low-stock")
def low_stock():
    return {"items":[{"id":k,"name":v["name"],"qty":v["qty"],"min":v["min_qty"]}
                     for k,v in INVENTORY.items() if v["qty"]<=v["min_qty"]]}

@app.post("/api/inventory")
async def add_inv(r: Request):
    d=await r.json()
    iid=str(uuid.uuid4())[:8]
    INVENTORY[iid]={"id":iid,"part_number":d.get("part_number",""),"name":d.get("name",""),
                    "category":d.get("category",""),"qty":int(d.get("qty",0)),
                    "min_qty":int(d.get("min_qty",5)),"cost_price":float(d.get("cost_price",0)),
                    "sell_price":float(d.get("sell_price",0)),"supplier":d.get("supplier",""),
                    "created":today()}
    return {"success":True,"item":INVENTORY[iid]}

@app.post("/api/inventory/{iid}/adjust")
async def adj_inv(iid: str, r: Request):
    d=await r.json()
    if iid not in INVENTORY: raise HTTPException(404)
    INVENTORY[iid]["qty"]=max(0,INVENTORY[iid]["qty"]+int(d.get("delta",0)))
    return {"success":True,"item":INVENTORY[iid]}

@app.delete("/api/inventory/{iid}")
def del_inv(iid: str):
    if iid not in INVENTORY: raise HTTPException(404)
    del INVENTORY[iid]; return {"success":True}

# PURCHASE ORDERS
@app.get("/api/purchase-orders")
def list_pos(): return {"pos":list(PURCHASE_ORDERS.values())}

@app.post("/api/purchase-orders")
async def create_po(r: Request):
    d=await r.json()
    pid=str(len(PURCHASE_ORDERS)+1).zfill(4)
    PURCHASE_ORDERS[pid]={"id":pid,"supplier":d.get("supplier",""),"items":d.get("items",""),
                          "total":float(d.get("total",0)),"status":"pending","created":now()}
    return {"success":True,"po":PURCHASE_ORDERS[pid]}

@app.put("/api/purchase-orders/{pid}")
async def update_po(pid: str, r: Request):
    d=await r.json()
    if pid not in PURCHASE_ORDERS: raise HTTPException(404)
    PURCHASE_ORDERS[pid]["status"]=d.get("status","pending")
    return {"success":True,"po":PURCHASE_ORDERS[pid]}

@app.delete("/api/purchase-orders/{pid}")
def del_po(pid: str):
    if pid not in PURCHASE_ORDERS: raise HTTPException(404)
    del PURCHASE_ORDERS[pid]; return {"success":True}

# STAFF
@app.get("/api/staff")
def list_staff(): return {"staff":list(STAFF.values())}

@app.post("/api/staff")
async def add_staff(r: Request):
    d=await r.json()
    sid=str(uuid.uuid4())[:8]
    STAFF[sid]={"id":sid,"name":d.get("name",""),"role":d.get("role",""),
                "phone":d.get("phone",""),"email":d.get("email",""),
                "hourly_rate":float(d.get("hourly_rate",150)),"created":today()}
    return {"success":True,"staff":STAFF[sid]}

@app.delete("/api/staff/{sid}")
def del_staff(sid: str):
    if sid not in STAFF: raise HTTPException(404)
    del STAFF[sid]; return {"success":True}

# CLOCK IN/OUT
@app.get("/api/clockins")
def list_clockins(): return {"clockins":list(CLOCKINS.values())}

@app.post("/api/clockins")
async def clock_in(r: Request):
    d=await r.json()
    cid=str(uuid.uuid4())[:8]
    CLOCKINS[cid]={"id":cid,"staff_id":d.get("staff_id",""),
                   "clock_in":now(),"clock_out":None}
    return {"success":True,"clockin":CLOCKINS[cid]}

@app.post("/api/clockins/{sid}/out")
async def clock_out(sid: str):
    for c in CLOCKINS.values():
        if c["staff_id"]==sid and not c["clock_out"]:
            c["clock_out"]=now()
            return {"success":True,"clockin":c}
    raise HTTPException(404,"No active clock-in")

# EXPENSES
@app.get("/api/expenses")
def list_exp(): return {"expenses":list(EXPENSES.values())}

@app.post("/api/expenses")
async def add_exp(r: Request):
    d=await r.json()
    eid=str(uuid.uuid4())[:8]
    EXPENSES[eid]={"id":eid,"category":d.get("category","Other"),
                   "amount":float(d.get("amount",0)),
                   "date":d.get("date",today()),"note":d.get("note",""),
                   "created":now()}
    return {"success":True,"expense":EXPENSES[eid]}

@app.delete("/api/expenses/{eid}")
def del_exp(eid: str):
    if eid not in EXPENSES: raise HTTPException(404)
    del EXPENSES[eid]; return {"success":True}

# REMINDERS
@app.get("/api/reminders")
def get_reminders():
    reminders=[]
    for j in JOBS.values():
        if j.get("km",0)>0 and j["status"]=="Completed":
            due_km=j["km"]+10000
            reminders.append({"vehicle":j["vehicle"],"customer":j["customer"],
                              "phone":j.get("phone",""),"last_service":j["created"][:10],
                              "last_km":j["km"],"due":f"at {due_km} km or 6 months"})
    return {"reminders":reminders[:20]}

# CSV EXPORTS
@app.get("/api/export/jobs")
def exp_jobs():
    o=io.StringIO(); w=csv.writer(o)
    w.writerow(["Job ID","Customer","Vehicle","Reg","Complaint","Assigned","Status","Total","Created"])
    for j in JOBS.values():
        w.writerow([j["id"],j["customer"],j["vehicle"],j.get("registration",""),
                    j["complaint"],j.get("assigned_to",""),j["status"],j.get("total",0),j["created"]])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]),media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=jobs.csv"})

@app.get("/api/export/customers")
def exp_cust():
    o=io.StringIO(); w=csv.writer(o)
    w.writerow(["Name","Phone","Email","Address","Created"])
    for c in CUSTOMERS.values():
        w.writerow([c["name"],c["phone"],c.get("email",""),c.get("address",""),c["created"]])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]),media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=customers.csv"})

@app.get("/api/export/tax")
def exp_tax(from_date: str = None, to_date: str = None):
    o=io.StringIO(); w=csv.writer(o)
    w.writerow(["Date","Type","Description","Amount","VAT"])
    for i in INVOICES.values():
        if from_date and i["created"][:10]<from_date: continue
        if to_date and i["created"][:10]>to_date: continue
        w.writerow([i["created"][:10],"Income",i["description"],i["total"],i["vat"]])
    for e in EXPENSES.values():
        if from_date and e["date"]<from_date: continue
        if to_date and e["date"]>to_date: continue
        w.writerow([e["date"],"Expense",e["category"]+" - "+e.get("note",""),-e["amount"],0])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]),media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=tax_report.csv"})
