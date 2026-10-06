from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from datetime import datetime, timedelta
import openai, os, json, uuid, csv, io
from workshop_routes import router as workshop_router
from workshop_api import router as workshop_api_router
from ai_panel import AI_PANEL_HTML
from ai_endpoints import router as ai_router
import os

import db
from data import (FAULT_CODES, WMI_DB, YEAR_CODES, TORQUE_SPECS, TORQUE_SEQUENCES,
                  PARTS_CATALOG, COMMON_PROBLEMS, WIRING_LIBRARY, OBD_PIDS,
                  BULB_CHART, BATTERY_SIZES, TYRE_SIZES, FUSE_BOXES,
                  INSPECTION_CATEGORIES, SERVICE_INTERVALS, TRANSLATIONS)
from pages import HTML_PAGE

app = FastAPI(title="RamsTech")
app.include_router(ai_router)
app.include_router(workshop_api_router)
app.include_router(workshop_router)
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
db.init()

MEM = {k: {} for k in ["jobs","customers","appointments","quotes","invoices",
                       "inventory","purchase_orders","staff","clockins","expenses",
                       "fuel_logs"]}
WORKSHOP = {"name":"My Workshop","phone":"","address":"","email":"","logo":"🔧","labour_rate":450}

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M")
def today(): return datetime.now().strftime("%Y-%m-%d")

def store_list(t):
    if db.is_ready(): return db.get_all(t)
    return list(MEM[t].values())
def store_get(t,i):
    if db.is_ready(): return db.get_one(t,i)
    return MEM[t].get(i)
def store_save(t,i,row):
    if db.is_ready():
        return db.update(t,i,row) if db.get_one(t,i) else db.insert(t,row)
    MEM[t][i]=row; return row
def store_delete(t,i):
    if db.is_ready(): return db.delete(t,i)
    MEM[t].pop(i,None); return True
def get_workshop_data():
    if db.is_ready():
        w=db.get_workshop()
        if w: return w
    return WORKSHOP
def save_workshop_data(d):
    if db.is_ready(): return db.save_workshop(d)
    WORKSHOP.update(d); return d

@app.get("/", response_class=HTMLResponse)
async def home(): return HTML_PAGE.replace("</body>", AI_PANEL_HTML + "</body>")

@app.get("/health")
@app.get("/debug/env")
def debug_env():
    return {
        "SUPABASE_URL_set": bool(os.getenv("SUPABASE_URL", "").strip()),
        "SUPABASE_URL_starts_with_https": os.getenv("SUPABASE_URL", "").strip().startswith("https://"),
        "SUPABASE_URL_length": len(os.getenv("SUPABASE_URL", "").strip()),
        "SUPABASE_SERVICE_KEY_set": bool(os.getenv("SUPABASE_SERVICE_KEY", "").strip()),
        "SUPABASE_SERVICE_KEY_length": len(os.getenv("SUPABASE_SERVICE_KEY", "").strip()),
        "OPENAI_API_KEY_set": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "GROQ_API_KEY_set": bool(os.getenv("GROQ_API_KEY", "").strip()),
        "OLP_API_KEY_set": bool(os.getenv("OLP_API_KEY", "").strip()),
    }
def health():
    return {"status":"healthy","database":("supabase" if db.is_ready() else "memory"),
            "time":datetime.now().isoformat()}

# ═══════════════════════════════════
# TRANSLATIONS
# ═══════════════════════════════════
@app.get("/api/translations/{lang}")
def get_translations(lang: str):
    return {"lang":lang,"strings":TRANSLATIONS.get(lang,TRANSLATIONS["en"])}

# STATS
@app.get("/api/stats")
def get_stats():
    jobs=store_list("jobs"); invs=store_list("invoices"); exps=store_list("expenses")
    custs=store_list("customers")
    rev=sum(float(i.get("total",0)) for i in invs)
    exp=sum(float(e.get("amount",0)) for e in exps)
    labels,data=[],[]
    for i in range(6,-1,-1):
        day=(datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(day[5:])
        data.append(round(sum(float(x.get("total",0)) for x in invs if (x.get("created") or "").startswith(day)),2))
    return {"jobs_total":len(jobs),"jobs_open":sum(1 for j in jobs if j.get("status")!="Completed"),
            "jobs_completed":sum(1 for j in jobs if j.get("status")=="Completed"),
            "jobs_new":sum(1 for j in jobs if j.get("status")=="New"),
            "jobs_progress":sum(1 for j in jobs if j.get("status")=="In Progress"),
            "customers":len(custs),"revenue":round(rev,2),"expenses":round(exp,2),
            "revenue_labels":labels,"revenue_data":data}

@app.get("/api/analytics")
def get_analytics():
    invs=store_list("invoices"); exps=store_list("expenses"); jobs=store_list("jobs")
    tr=sum(float(i.get("total",0)) for i in invs)
    te=sum(float(e.get("amount",0)) for e in exps)
    avg=tr/len(invs) if invs else 0
    svc={}
    for j in jobs:
        c=(j.get("complaint") or "").strip()[:30]
        if c: svc[c]=svc.get(c,0)+1
    top_services=[{"name":k,"count":v} for k,v in sorted(svc.items(),key=lambda x:-x[1])[:5]]
    cr={}
    for i in invs:
        n=i.get("customer","")
        if n: cr[n]=cr.get(n,0)+float(i.get("total",0))
    top_customers=[{"name":k,"total":v} for k,v in sorted(cr.items(),key=lambda x:-x[1])[:5]]
    return {"total_revenue":tr,"total_expenses":te,"net_profit":tr-te,
            "avg_invoice":avg,"top_services":top_services,"top_customers":top_customers}

@app.get("/api/workshop")
def get_workshop(): return get_workshop_data()

@app.post("/api/workshop")
async def save_workshop(r: Request):
    d=await r.json(); save_workshop_data(d)
    return {"success":True,"workshop":get_workshop_data()}

# AI CONTEXT-AWARE CHAT
# ═══════════════════════════════════════════
@app.post("/api/ai-context")
async def ai_context(r: Request):
    d = await r.json()
    message = (d.get("message") or "").strip()
    active_tab = (d.get("active_tab") or "").strip()
    vehicle = (d.get("vehicle") or "").strip()
    if not message:
        raise HTTPException(400, "message is required")

    # ─── Build tab-specific context from data.py ───
    context_lines = []

    def trim(obj, max_chars=3000):
        """Convert dict/list to a compact string, safely truncated."""
        try:
            import json as _json
            s = _json.dumps(obj, default=str)
            return s[:max_chars]
        except Exception:
            return str(obj)[:max_chars]

    if active_tab in ("fault_codes", "faults", "dtc"):
        # Only inject codes that match keywords in the user's question
        q = message.lower()
        hits = {}
        for code, info in FAULT_CODES.items():
            text = (code + " " + str(info.get("description", ""))).lower()
            if code.lower() in q or any(w in text for w in q.split() if len(w) > 3):
                hits[code] = info.get("description", "")
            if len(hits) >= 15:
                break
        if hits:
            context_lines.append("Fault codes matching the question: " + trim(hits))

    if active_tab in ("obd", "obd_pids", "pids"):
        context_lines.append("OBD-II PIDs (reference): " + trim(OBD_PIDS))

    if active_tab in ("wiring", "circuits"):
        context_lines.append("Wiring library circuits: " + trim(WIRING_LIBRARY))

    if active_tab in ("torque", "torque_specs"):
        q = message.lower()
        hits = {k: v for k, v in TORQUE_SPECS.items()
                if any(w in k.lower() for w in q.split() if len(w) > 3)}
        if not hits:
            # If no keyword match, send a small sample so AI knows the data format
            sample = dict(list(TORQUE_SPECS.items())[:20])
            context_lines.append("Torque specs (sample of local database): " + trim(sample))
        else:
            context_lines.append("Torque specs matching the question: " + trim(hits))
        context_lines.append("Torque sequences: " + trim(TORQUE_SEQUENCES))

    if active_tab in ("bulbs", "bulb_chart"):
        context_lines.append("Bulb chart: " + trim(BULB_CHART))

    if active_tab in ("batteries", "battery_sizes"):
        context_lines.append("Battery sizes: " + trim(BATTERY_SIZES))

    if active_tab in ("tyres", "tyre_sizes"):
        context_lines.append("Tyre sizes: " + trim(TYRE_SIZES))

    if active_tab in ("fuses", "fuse_boxes"):
        context_lines.append("Fuse boxes: " + trim(FUSE_BOXES))

    if active_tab in ("service", "service_calc", "service_intervals"):
        context_lines.append("Service intervals: " + trim(SERVICE_INTERVALS))

    if active_tab in ("checklists", "inspection"):
        context_lines.append("Inspection categories: " + trim(INSPECTION_CATEGORIES))

    if active_tab in ("problems", "common_problems"):
        context_lines.append("Common problems: " + trim(COMMON_PROBLEMS))

    if active_tab in ("parts", "parts_catalog"):
        context_lines.append("Parts catalog: " + trim(PARTS_CATALOG))

    if active_tab in ("vin", "vin_decoder"):
        context_lines.append("WMI database: " + trim(WMI_DB))
        context_lines.append("Year codes: " + trim(YEAR_CODES))

    # If on fault codes tab, and the message contains a fault code, use the fault endpoint logic too
    fault_hint = ""
    import re
    codes = re.findall(r"\b[PBCU]\d{4}\b", message.upper())
    if codes:
        olp_key = os.getenv("OLP_API_KEY", "").strip()
        for code in codes[:2]:
            local = FAULT_CODES.get(code) or {}
            if local.get("description"):
                fault_hint += f"\n{code}: {local['description']}"
            elif olp_key:
                try:
                    import httpx
                    with httpx.Client(timeout=8.0) as client:
                        resp = client.get(
                            f"https://openlaborproject.com/api/v1/dtc/{code}",
                            headers={"x-api-key": olp_key}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            fault_hint += f"\n{code}: {data.get('description','')}"
                except Exception:
                    pass

    # ─── Assemble final prompt ───
    tab_label = active_tab.replace("_", " ").title() if active_tab else "General"
    context_block = "\n\n".join(context_lines) if context_lines else "No tab-specific data."

    system_msg = (
        "You are RamsTech AI, a master mechanic and diagnostic expert for South African "
        "workshops. The user is currently on the '" + tab_label + "' diagnostic tab. "
        "Use any LOCAL DATA provided below as authoritative — quote exact numbers, part "
        "codes, torque specs, PIDs, fuse ratings, etc. from it. If local data does not "
        "cover the question, use your own expert knowledge but say clearly that the value "
        "is from general knowledge, not from the local database. Never invent torque "
        "specs, fuse ratings, or part numbers. Use ZAR for costs. Include safety warnings "
        "where relevant."
    )

    user_msg = (
        f"Active diagnostic tab: {tab_label}\n"
        f"Vehicle: {vehicle or 'not specified'}"
        + (f"\n\nLocal data:\n{context_block}" if context_lines else "")
        + (f"\n\nFault code references:{fault_hint}" if fault_hint else "")
        + f"\n\nQuestion: {message}"
    )

    if not OPENAI_KEY and not os.getenv("GROQ_API_KEY", "").strip():
        return {
            "success": False,
            "reply": "AI not configured. Add OPENAI_API_KEY or GROQ_API_KEY in Render.",
        }

    try:
        import workshop_ai
        reply, provider = workshop_ai.chat(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=1100,
        )
        return {
            "success": True,
            "reply": reply,
            "provider": provider,
            "tab": tab_label,
            "context_items": len(context_lines),
        }
    except Exception as e:
        return {"success": False, "reply": f"AI error: {str(e)}"}
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
    d=await r.json(); km=int(d.get("current_km",0)); vt=d.get("vehicle_type","petrol")
    cfg=SERVICE_INTERVALS.get(vt,SERVICE_INTERVALS["petrol"])
    return {"next_service_km":((km//cfg["km"])+1)*cfg["km"],
            "months_interval":cfg["months"],"items":cfg["items"]}

@app.post("/api/bolt-calc")
async def bolt_calc(r: Request):
    d=await r.json(); size=d.get("size","M8"); grade=d.get("grade","8.8"); cond=d.get("condition","dry")
    tm={"8.8":800,"10.9":1040,"12.9":1220}
    am={"M6":20.1,"M8":36.6,"M10":58.0,"M12":84.3,"M14":115.0,"M16":157.0,"M18":192.0,"M20":245.0}
    km={"dry":0.20,"oiled":0.17,"moly":0.14}
    ts=tm.get(grade,800); a=am.get(size,36.6); k=km.get(cond,0.20)
    cf=0.75*ts*a; dm=float(size.replace("M",""))/1000.0; nm=k*dm*cf
    return {"size":size,"grade":grade,"condition":cond,"nm":nm,"ftlb":nm*0.73756,"clamp_kn":cf/1000}

@app.get("/api/vin/{vin}")
def decode_vin(vin: str):
    v=vin.strip().upper()
    if len(v)!=17: raise HTTPException(400,"VIN must be 17 characters")
    m,c=WMI_DB.get(v[:3],("Unknown","Unknown"))
    return {"vin":v,"manufacturer":m,"country":c,"year":YEAR_CODES.get(v[9],"Unknown")}

# AI
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

@app.post("/api/paint/match")
async def match_paint(r: Request):
    d=await r.json(); img=d.get("image_base64",""); veh=d.get("vehicle_info","")
    if not img: raise HTTPException(400,"Image required")
    if not OPENAI_KEY: return {"success":False,"error":"AI not configured"}
    if img.startswith("data:"): img=img.split(",",1)[1]
    if len(img)>7000000: return {"success":False,"error":"Image too large"}
    prompt=f"""Expert paint tech. Vehicle: {veh or 'N/A'}
Respond ONLY valid JSON:
{{"detected_colour":{{"name":"N","hex_code":"#RRGGBB","rgb":[R,G,B],"finish":"Solid|Metallic|Pearl","colour_family":"White|Black|Red|Blue|Silver|Grey"}},"confidence":"High|Medium|Low","brand_codes":[{{"brand":"DuPont","code":"C","name":"F"}}],"mixing_formula":{{"base_colour":"D","toners":[{{"name":"T","parts":"X"}}],"reducer":"R"}},"safety_warnings":["W"]}}"""
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
def list_jobs(): return {"jobs":store_list("jobs")}

@app.post("/api/jobs")
async def create_job(r: Request):
    d=await r.json()
    jid=str(uuid.uuid4())[:8]
    job={"id":jid,"customer":d.get("customer",""),"phone":d.get("phone",""),
         "vehicle":d.get("vehicle",""),"registration":d.get("registration",""),
         "km":int(d.get("km",0)),"complaint":d.get("complaint",""),
         "assigned_to":d.get("assigned_to",""),"photos":d.get("photos",[])[:5],
         "signature":d.get("signature",""),
         "warranty_months":int(d.get("warranty_months",6)),"status":"New",
         "timeline":[now()+" — Job created"],
         "labour_hours":0,"labour_rate":get_workshop_data().get("labour_rate",450),
         "parts_cost":0,"labour_cost":0,"subtotal":0,"vat":0,"total":0,"created":now()}
    store_save("jobs",jid,job)
    return {"success":True,"job":job}

@app.put("/api/jobs/{jid}")
async def update_job(jid: str, r: Request):
    d=await r.json()
    job=store_get("jobs",jid)
    if not job: raise HTTPException(404)
    if "status" in d: job["status"]=d["status"]
    if "note" in d:
        tl=job.get("timeline") or []
        tl.append(now()+" — "+d["note"])
        job["timeline"]=tl
    store_save("jobs",jid,job)
    return {"success":True,"job":job}

@app.post("/api/jobs/{jid}/cost")
async def set_cost(jid: str, r: Request):
    d=await r.json()
    job=store_get("jobs",jid)
    if not job: raise HTTPException(404)
    h=float(d.get("labour_hours",0)); rate=float(d.get("labour_rate",450))
    parts=float(d.get("parts_cost",0))
    labour=h*rate; subtotal=labour+parts; vat=subtotal*0.15; total=subtotal+vat
    job.update({"labour_hours":h,"labour_rate":rate,"parts_cost":parts,
                "labour_cost":labour,"subtotal":subtotal,"vat":vat,"total":total})
    tl=job.get("timeline") or []
    tl.append(now()+f" — Cost: R{total:.2f}")
    job["timeline"]=tl
    store_save("jobs",jid,job)
    return {"success":True,"job":job}

# CUSTOMERS
@app.get("/api/customers")
def list_customers(): return {"customers":store_list("customers")}

@app.post("/api/customers")
async def create_customer(r: Request):
    d=await r.json()
    cid=str(uuid.uuid4())[:8]
    c={"id":cid,"name":d.get("name",""),"phone":d.get("phone",""),
       "email":d.get("email",""),"address":d.get("address",""),"created":today()}
    store_save("customers",cid,c)
    return {"success":True,"customer":c}

# APPOINTMENTS
@app.get("/api/appointments")
def list_appts(): return {"appointments":store_list("appointments")}

@app.post("/api/appointments")
async def create_appt(r: Request):
    d=await r.json()
    aid=str(uuid.uuid4())[:8]
    a={"id":aid,**{k:d.get(k,"") for k in ["customer","phone","vehicle","service","date","time"]}}
    store_save("appointments",aid,a)
    return {"success":True,"appointment":a}

@app.delete("/api/appointments/{aid}")
def del_appt(aid: str):
    store_delete("appointments",aid); return {"success":True}

# QUOTES
@app.get("/api/quotes")
def list_quotes(): return {"quotes":store_list("quotes")}

@app.post("/api/quotes")
async def create_quote(r: Request):
    d=await r.json()
    qid=str(uuid.uuid4())[:8]
    labour=float(d.get("labour",0)); parts=float(d.get("parts",0))
    subtotal=labour+parts; vat=subtotal*0.15; total=subtotal+vat
    q={"id":qid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),
       "description":d.get("description",""),"labour":labour,"parts":parts,
       "subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    store_save("quotes",qid,q)
    return {"success":True,"quote":q}

@app.post("/api/quotes/{qid}/accept")
async def accept_quote(qid: str):
    q=store_get("quotes",qid)
    if not q: raise HTTPException(404)
    iid=str(uuid.uuid4())[:8]
    i={"id":iid,"customer":q["customer"],"vehicle":q["vehicle"],
       "description":q["description"],"labour":q["labour"],"parts":q["parts"],
       "subtotal":q["subtotal"],"vat":q["vat"],"total":q["total"],
       "amount_paid":0,"paid":False,"created":now()}
    store_save("invoices",iid,i)
    store_delete("quotes",qid)
    return {"success":True,"invoice":i}

@app.delete("/api/quotes/{qid}")
def del_quote(qid: str):
    store_delete("quotes",qid); return {"success":True}

# INVOICES
@app.get("/api/invoices")
def list_invoices(): return {"invoices":store_list("invoices")}

@app.post("/api/invoices")
async def create_invoice(r: Request):
    d=await r.json()
    labour=float(d.get("labour",0)); parts=float(d.get("parts",0))
    subtotal=labour+parts; vat=subtotal*0.15; total=subtotal+vat
    iid=str(uuid.uuid4())[:8]
    i={"id":iid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),
       "description":d.get("description",""),"labour":labour,"parts":parts,
       "subtotal":subtotal,"vat":vat,"total":total,"amount_paid":0,"paid":False,"created":now()}
    store_save("invoices",iid,i)
    return {"success":True,"invoice":i}

@app.post("/api/invoices/{iid}/pay")
async def record_payment(iid: str, r: Request):
    d=await r.json()
    inv=store_get("invoices",iid)
    if not inv: raise HTTPException(404)
    amt=float(d.get("amount",0))
    inv["amount_paid"]=float(inv.get("amount_paid",0))+amt
    inv["paid"]=inv["amount_paid"]>=float(inv["total"])
    store_save("invoices",iid,inv)
    return {"success":True,"invoice":inv}

# INVENTORY
@app.get("/api/inventory")
def list_inv(): return {"items":store_list("inventory")}

@app.get("/api/inventory/low-stock")
def low_stock():
    return {"items":[{"id":i["id"],"name":i["name"],"qty":int(i["qty"]),"min":int(i["min_qty"])}
                     for i in store_list("inventory") if int(i["qty"])<=int(i["min_qty"])]}

@app.post("/api/inventory")
async def add_inv(r: Request):
    d=await r.json()
    iid=str(uuid.uuid4())[:8]
    item={"id":iid,"part_number":d.get("part_number",""),"name":d.get("name",""),
          "category":d.get("category",""),"qty":int(d.get("qty",0)),
          "min_qty":int(d.get("min_qty",5)),"cost_price":float(d.get("cost_price",0)),
          "sell_price":float(d.get("sell_price",0)),"supplier":d.get("supplier",""),"created":today()}
    store_save("inventory",iid,item)
    return {"success":True,"item":item}

@app.post("/api/inventory/{iid}/adjust")
async def adj_inv(iid: str, r: Request):
    d=await r.json()
    item=store_get("inventory",iid)
    if not item: raise HTTPException(404)
    item["qty"]=max(0,int(item["qty"])+int(d.get("delta",0)))
    store_save("inventory",iid,item)
    return {"success":True,"item":item}

@app.delete("/api/inventory/{iid}")
def del_inv(iid: str):
    store_delete("inventory",iid); return {"success":True}

# PURCHASE ORDERS
@app.get("/api/purchase-orders")
def list_pos(): return {"pos":store_list("purchase_orders")}

@app.post("/api/purchase-orders")
async def create_po(r: Request):
    d=await r.json()
    pid=str(uuid.uuid4())[:8]
    po={"id":pid,"supplier":d.get("supplier",""),"items":d.get("items",""),
        "total":float(d.get("total",0)),"status":"pending","created":now()}
    store_save("purchase_orders",pid,po)
    return {"success":True,"po":po}

@app.put("/api/purchase-orders/{pid}")
async def update_po(pid: str, r: Request):
    d=await r.json()
    po=store_get("purchase_orders",pid)
    if not po: raise HTTPException(404)
    po["status"]=d.get("status","pending")
    store_save("purchase_orders",pid,po)
    return {"success":True,"po":po}

@app.delete("/api/purchase-orders/{pid}")
def del_po(pid: str):
    store_delete("purchase_orders",pid); return {"success":True}

# STAFF
@app.get("/api/staff")
def list_staff(): return {"staff":store_list("staff")}

@app.post("/api/staff")
async def add_staff(r: Request):
    d=await r.json()
    sid=str(uuid.uuid4())[:8]
    s={"id":sid,"name":d.get("name",""),"role":d.get("role",""),
       "phone":d.get("phone",""),"email":d.get("email",""),
       "hourly_rate":float(d.get("hourly_rate",150)),"created":today()}
    store_save("staff",sid,s)
    return {"success":True,"staff":s}

@app.delete("/api/staff/{sid}")
def del_staff(sid: str):
    store_delete("staff",sid); return {"success":True}

# CLOCKINS
@app.get("/api/clockins")
def list_clockins(): return {"clockins":store_list("clockins")}

@app.post("/api/clockins")
async def clock_in(r: Request):
    d=await r.json()
    cid=str(uuid.uuid4())[:8]
    c={"id":cid,"staff_id":d.get("staff_id",""),"clock_in":now(),"clock_out":None}
    store_save("clockins",cid,c)
    return {"success":True,"clockin":c}

@app.post("/api/clockins/{sid}/out")
async def clock_out(sid: str):
    for c in store_list("clockins"):
        if c["staff_id"]==sid and not c.get("clock_out"):
            c["clock_out"]=now()
            store_save("clockins",c["id"],c)
            return {"success":True,"clockin":c}
    raise HTTPException(404,"No active clock-in")

# EXPENSES
@app.get("/api/expenses")
def list_exp(): return {"expenses":store_list("expenses")}

@app.post("/api/expenses")
async def add_exp(r: Request):
    d=await r.json()
    eid=str(uuid.uuid4())[:8]
    e={"id":eid,"category":d.get("category","Other"),"amount":float(d.get("amount",0)),
       "date":d.get("date",today()),"note":d.get("note",""),"created":now()}
    store_save("expenses",eid,e)
    return {"success":True,"expense":e}

@app.delete("/api/expenses/{eid}")
def del_exp(eid: str):
    store_delete("expenses",eid); return {"success":True}

# REMINDERS
@app.get("/api/reminders")
def get_reminders():
    reminders=[]
    for j in store_list("jobs"):
        if int(j.get("km",0))>0 and j.get("status")=="Completed":
            due=int(j["km"])+10000
            reminders.append({"vehicle":j["vehicle"],"customer":j["customer"],
                              "phone":j.get("phone",""),"last_service":(j.get("created") or "")[:10],
                              "last_km":j["km"],"due":f"at {due} km or 6 months"})
    return {"reminders":reminders[:20]}

# ═══════════════════════════════════
# FUEL LOG (v9.0)
# ═══════════════════════════════════
@app.get("/api/fuel")
def list_fuel(): return {"logs":store_list("fuel_logs")}

@app.post("/api/fuel")
async def add_fuel(r: Request):
    d=await r.json()
    fid=str(uuid.uuid4())[:8]
    km=int(d.get("km",0)); litres=float(d.get("litres",0)); cost=float(d.get("cost",0))
    # Calculate consumption if previous entry exists for same vehicle
    prev=[x for x in store_list("fuel_logs") if x.get("vehicle")==d.get("vehicle","")]
    consumption=0
    if prev:
        prev_km=max(int(x.get("km",0)) for x in prev)
        if km>prev_km: consumption=round((litres/(km-prev_km))*100,2)
    log={"id":fid,"vehicle":d.get("vehicle",""),"km":km,"litres":litres,"cost":cost,
         "consumption":consumption,"station":d.get("station",""),"date":d.get("date",today())}
    store_save("fuel_logs",fid,log)
    return {"success":True,"log":log}

@app.delete("/api/fuel/{fid}")
def del_fuel(fid: str):
    store_delete("fuel_logs",fid); return {"success":True}

# ═══════════════════════════════════
# WARRANTY TRACKER (v9.0)
# ═══════════════════════════════════
@app.get("/api/warranty")
def get_warranty():
    from datetime import datetime as dt
    items=[]
    for j in store_list("jobs"):
        if j.get("status")=="Completed" and int(j.get("warranty_months",0))>0:
            try:
                done=dt.strptime((j.get("created") or "")[:10],"%Y-%m-%d")
                months=int(j["warranty_months"])
                # Calculate expiry
                year=done.year + (done.month + months - 1) // 12
                month=((done.month + months - 1) % 12) + 1
                expiry=done.replace(year=year,month=month)
                days_left=(expiry-dt.now()).days
                items.append({"id":j["id"],"customer":j["customer"],"vehicle":j["vehicle"],
                              "phone":j.get("phone",""),"job_date":(j.get("created") or "")[:10],
                              "months":months,"expiry":expiry.strftime("%Y-%m-%d"),
                              "days_left":days_left,"status":"active" if days_left>0 else "expired"})
            except Exception: pass
    items.sort(key=lambda x:x["days_left"])
    return {"warranties":items}

# CSV EXPORTS
@app.get("/api/export/jobs")
def exp_jobs():
    o=io.StringIO(); w=csv.writer(o)
    w.writerow(["Job ID","Customer","Vehicle","Reg","Complaint","Assigned","Status","Total","Created"])
    for j in store_list("jobs"):
        w.writerow([j["id"],j["customer"],j["vehicle"],j.get("registration",""),
                    j["complaint"],j.get("assigned_to",""),j["status"],j.get("total",0),j["created"]])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]),media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=jobs.csv"})

@app.get("/api/export/customers")
def exp_cust():
    o=io.StringIO(); w=csv.writer(o)
    w.writerow(["Name","Phone","Email","Address","Created"])
    for c in store_list("customers"):
        w.writerow([c["name"],c["phone"],c.get("email",""),c.get("address",""),c["created"]])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]),media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=customers.csv"})

@app.get("/api/export/tax")
def exp_tax(from_date: str = None, to_date: str = None):
    o=io.StringIO(); w=csv.writer(o)
    w.writerow(["Date","Type","Description","Amount","VAT"])
    for i in store_list("invoices"):
        d=(i.get("created") or "")[:10]
        if from_date and d<from_date: continue
        if to_date and d>to_date: continue
        w.writerow([d,"Income",i["description"],i["total"],i.get("vat",0)])
    for e in store_list("expenses"):
        if from_date and e["date"]<from_date: continue
        if to_date and e["date"]>to_date: continue
        w.writerow([e["date"],"Expense",e["category"]+" - "+e.get("note",""),-float(e["amount"]),0])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]),media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=tax_report.csv"})
