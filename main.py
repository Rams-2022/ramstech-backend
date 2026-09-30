# main.py — RamsTech complete single-file app
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from datetime import datetime, timedelta
import openai, os, uuid, csv, io, json

app = FastAPI(title="RamsTech", version="18.0")

# ═══════════════════════════════════════════════
# CORS — allow all origins
# ═══════════════════════════════════════════════
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
MAX_IMAGE_SIZE = 7_000_000

# ═══════════════════════════════════════════════
# ⚡ FAST HEALTH CHECK — RESPONDS IN MILLISECONDS
# NO database, NO external calls, NO slow code
# ═══════════════════════════════════════════════
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}

# Also respond fast on root of API to help wake-up pingers
@app.head("/health")
def health_head():
    return {}

# ═══════════════════════════════════════════════
# DATABASE LAYER (Supabase + memory fallback)
# ═══════════════════════════════════════════════
_db = None
DB_READY = False
MEM = {
    "jobs":{}, "customers":{}, "invoices":{}, "quotes":{}, "appointments":{},
    "inventory":{}, "staff":{}, "expenses":{}, "suppliers":{}
}
WORKSHOP = {
    "name":"My Workshop","phone":"","email":"","address":"","hours":"",
    "logo":"🔧","labour_rate":450,"vat_number":"","company_reg":"",
    "bank_details":"","terms":"Payment due within 30 days. Parts warranty per manufacturer. Labour warranty 6 months."
}

def init_db():
    global _db, DB_READY
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[db] Memory mode")
        return
    try:
        from supabase import create_client
        _db = create_client(SUPABASE_URL, SUPABASE_KEY)
        _db.table("workshop").select("id").limit(1).execute()
        DB_READY = True
        print("[db] Supabase connected")
    except Exception as e:
        print(f"[db] Failed: {e}")
        DB_READY = False

def db_list(t):
    if DB_READY:
        try: return _db.table(t).select("*").execute().data or []
        except Exception as e: print(f"[db] {t}: {e}")
    return list(MEM[t].values())

def db_get(t, i):
    if DB_READY:
        try:
            r = _db.table(t).select("*").eq("id", i).execute()
            return r.data[0] if r.data else None
        except Exception as e: print(f"[db] get {t}: {e}")
    return MEM[t].get(i)

def db_save(t, i, row):
    if DB_READY:
        try:
            if db_get(t, i): _db.table(t).update(row).eq("id", i).execute()
            else: _db.table(t).insert(row).execute()
            return row
        except Exception as e: print(f"[db] save {t}: {e}")
    MEM[t][i] = row
    return row

def db_del(t, i):
    if DB_READY:
        try: _db.table(t).delete().eq("id", i).execute(); return True
        except Exception as e: print(f"[db] del {t}: {e}"); return False
    MEM[t].pop(i, None); return True

def ws_get():
    if DB_READY:
        try:
            r = _db.table("workshop").select("*").eq("id", 1).execute()
            if r.data: return r.data[0]
        except Exception as e: print(f"[db] ws: {e}")
    return WORKSHOP

def ws_save(d):
    if DB_READY:
        try: _db.table("workshop").update(d).eq("id", 1).execute(); return d
        except Exception as e: print(f"[db] ws save: {e}")
    WORKSHOP.update(d); return WORKSHOP

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M")
def today(): return datetime.now().strftime("%Y-%m-%d")

# ═══════════════════════════════════════════════
# STATIC DATA
# ═══════════════════════════════════════════════
FAULT_CODES = {
    "P0101":{"code":"P0101","description":"Mass Air Flow Circuit","system":"Engine","severity":"Medium","causes":["Dirty MAF","Air leaks","Clogged filter"],"steps":["Check filter","Inspect intake","Clean MAF"]},
    "P0300":{"code":"P0300","description":"Multiple Cylinder Misfire","system":"Engine","severity":"High","causes":["Faulty plugs","Bad coils","Fuel issues"],"steps":["Scan cylinders","Check plugs","Test coils"]},
    "P0401":{"code":"P0401","description":"EGR Flow Insufficient","system":"Engine","severity":"Medium","causes":["Clogged EGR","Blocked passages"],"steps":["Inspect EGR","Check passages"]},
    "P0700":{"code":"P0700","description":"Transmission Control","system":"Transmission","severity":"High","causes":["Internal fault","TCM problem","Solenoid"],"steps":["Scan TCM","Check fluid"]},
    "P0087":{"code":"P0087","description":"Fuel Rail Pressure Low","system":"Diesel","severity":"High","causes":["Faulty HP pump","Clogged filter"],"steps":["Check pressure","Inspect filter"]},
    "HYD-001":{"code":"HYD-001","description":"Low Hydraulic Pressure","system":"Hydraulic","severity":"High","causes":["Worn pump","Leaks","Low fluid"],"steps":["Check fluid","Test pressure"]},
    "PNEU-001":{"code":"PNEU-001","description":"Air Compressor No Pressure","system":"Pneumatic","severity":"High","causes":["Worn rings","Leaking valves"],"steps":["Check belt","Test output"]},
}
WMI_DB = {"1HG":("Honda","USA"),"1FT":("Ford","USA"),"JHM":("Honda","Japan"),"JTD":("Toyota","Japan"),"JTM":("Toyota","Japan"),"KMH":("Hyundai","Korea"),"KNA":("Kia","Korea"),"WBA":("BMW","Germany"),"WDB":("Mercedes-Benz","Germany"),"WVW":("Volkswagen","Germany"),"YV1":("Volvo","Sweden"),"ZFA":("Fiat","Italy"),"AAV":("VW SA","South Africa"),"AHT":("Toyota SA","South Africa"),"AFA":("Ford SA","South Africa"),"ADB":("Mercedes SA","South Africa")}
YEAR_CODES = {"A":2010,"B":2011,"C":2012,"D":2013,"E":2014,"F":2015,"G":2016,"H":2017,"J":2018,"K":2019,"L":2020,"M":2021,"N":2022,"P":2023,"R":2024,"Y":2000,"1":2001,"2":2002,"3":2003,"4":2004,"5":2005,"6":2006,"7":2007,"8":2008,"9":2009}

TORQUE = [
    {"s":"M6","g":"8.8","nm":10,"ft":7.4,"u":"Small brackets"},{"s":"M8","g":"8.8","nm":25,"ft":18.4,"u":"Engine brackets"},
    {"s":"M10","g":"8.8","nm":50,"ft":37,"u":"Subframe bolts"},{"s":"M12","g":"8.8","nm":90,"ft":66,"u":"Wheel hubs"},
    {"s":"M14","g":"8.8","nm":140,"ft":103,"u":"Heavy brackets"},{"s":"M16","g":"8.8","nm":215,"ft":159,"u":"Chassis bolts"},
    {"s":"M20","g":"8.8","nm":425,"ft":313,"u":"Truck chassis"},{"s":"M8","g":"10.9","nm":35,"ft":25.8,"u":"Head (small)"},
    {"s":"M10","g":"10.9","nm":70,"ft":51.6,"u":"Head bolts"},{"s":"M12","g":"10.9","nm":120,"ft":88.5,"u":"Head bolts"},
    {"s":"M14","g":"10.9","nm":190,"ft":140,"u":"Diesel head"},{"s":"M16","g":"10.9","nm":295,"ft":218,"u":"Heavy diesel"},
    {"s":"M12","g":"12.9","nm":145,"ft":107,"u":"Racing"},{"s":"M10","g":"12.9","nm":83,"ft":61.2,"u":"Performance"},
]
SEQ = [
    {"c":"Cylinder Head — 4 Cyl","p":"Star","st":["Stage 1: 40 Nm","Stage 2: 80 Nm","Stage 3: +90°","Stage 4: +90°"],"n":"Replace TTY bolts."},
    {"c":"Wheel Nuts — Car","p":"Star","st":["Stage 1: 60 Nm","Final: 110 Nm"],"n":"Re-torque 50-100 km"},
    {"c":"Wheel Nuts — Bakkie","p":"Star","st":["Stage 1: 100 Nm","Final: 140 Nm"],"n":"Hilux, Ranger"},
    {"c":"Wheel Nuts — Truck","p":"Star","st":["Stage 1: 400 Nm","Stage 2: 500 Nm","Final: 600 Nm"],"n":"10-stud"},
    {"c":"Spark Plugs","p":"Linear","st":["Cast iron: 25 Nm","Aluminum: 18 Nm"],"n":"No overtighten"},
    {"c":"Oil Drain Plug","p":"Linear","st":["Steel M12: 25 Nm","Alum M12: 18 Nm"],"n":"New washer"},
]
BULBS = [
    {"v":"Toyota Hilux (2015+)","l":"H11","h":"HB3","f":"H16","r":"W16W"},
    {"v":"Ford Ranger","l":"H11","h":"HB3","f":"H11","r":"P21W"},
    {"v":"VW Polo","l":"H7","h":"H7","f":"H8","r":"P21W"},
    {"v":"BMW 3-Series","l":"H7 / Xenon","h":"H7","f":"H8","r":"P21W"},
    {"v":"Mercedes C-Class","l":"H7 / Xenon","h":"H7","f":"H11","r":"P21W"},
    {"v":"Isuzu D-Max","l":"H11","h":"HB3","f":"H11","r":"P21W"},
    {"v":"Nissan NP200","l":"H4","h":"H4","f":"H11","r":"P21W"},
    {"v":"Hyundai i20","l":"H7","h":"H7","f":"H27W","r":"P21W"},
]
BATTERIES = [
    {"v":"Toyota Hilux 2.8 GD-6","g":"DIN 66L","c":680,"a":70},
    {"v":"Ford Ranger 2.2 TDCi","g":"DIN 66L","c":660,"a":68},
    {"v":"VW Polo / Golf","g":"DIN 44L","c":330,"a":44},
    {"v":"BMW 3-Series","g":"DIN 80L","c":800,"a":80},
    {"v":"Mercedes C-Class","g":"DIN 80L","c":800,"a":80},
    {"v":"Isuzu D-Max","g":"DIN 66L","c":650,"a":68},
    {"v":"Land Cruiser 79","g":"DIN 88L ×2","c":880,"a":90},
    {"v":"Hyundai i20","g":"DIN 44L","c":350,"a":45},
    {"v":"Nissan Navara","g":"DIN 66L","c":640,"a":65},
    {"v":"Small bakkies (older)","g":"24F / 24R","c":500,"a":55},
]
TYRES = [
    {"v":"Toyota Hilux (current)","s":"265/65R17","f":"2.2 bar","r":"2.4 bar"},
    {"v":"Toyota Hilux (older)","s":"265/70R16","f":"2.0 bar","r":"2.2 bar"},
    {"v":"Ford Ranger","s":"265/65R17","f":"2.2 bar","r":"2.4 bar"},
    {"v":"VW Polo","s":"185/60R15","f":"2.1 bar","r":"2.1 bar"},
    {"v":"VW Golf 7","s":"205/55R16","f":"2.3 bar","r":"2.3 bar"},
    {"v":"BMW 3-Series","s":"225/45R18","f":"2.4 bar","r":"2.6 bar"},
    {"v":"Mercedes C-Class","s":"225/50R17","f":"2.3 bar","r":"2.5 bar"},
    {"v":"Hyundai i20","s":"185/65R15","f":"2.2 bar","r":"2.2 bar"},
    {"v":"Nissan NP200","s":"185/65R15","f":"2.0 bar","r":"2.2 bar"},
]
WIRING = [
    {"n":"Charging System","sy":"Charging","d":"Alternator, battery, warning light","c":["Battery 12V","Alternator","Ignition switch","Warning light"],"co":["Battery + → Alt B+ (Red, 6mm²)","Battery - → Ground","Alt D+ → Warning light","Warning light → IGN 15"],"nt":["Output: 13.8-14.4V"]},
    {"n":"Starting System","sy":"Starting","d":"Starter, relay, ignition","c":["Battery","Ignition switch","Starter relay","Starter motor"],"co":["Battery + → Starter 30 (25mm²)","IGN 50 → Relay 86","Relay 87 → Starter 50"],"nt":["Don't hold starter over 10 sec"]},
    {"n":"Engine Sensors","sy":"Engine","d":"MAF, MAP, TPS, ECT, O2","c":["ECU","MAF","MAP","TPS","ECT","O2"],"co":["ECU → MAF: signal+ground+power","ECU → MAP: signal+ground+5V","ECU → TPS: 5V+signal+ground"],"nt":["Reference: 4.9-5.1V"]},
    {"n":"Headlight Circuit","sy":"Lighting","d":"Relay-controlled","c":["Battery","Headlight switch","Low relay","High relay","Headlights"],"co":["Battery + → Relay 30","Switch 56 → Low relay 86","Relay 87 → Headlight +"],"nt":["Voltage drop < 0.5V"]},
    {"n":"ABS Wheel Sensors","sy":"ABS","d":"4-channel","c":["ABS ECU","FL/FR/RL/RR sensors","Pump motor"],"co":["ABS → FL (White+Black)","ABS → FR (Yellow+Green)","ABS → RL (Blue+Grey)","ABS → RR (Brown+Purple)"],"nt":["Resistance: 800-1400Ω"]},
    {"n":"Diesel Glow Plugs","sy":"Diesel","d":"Glow relay","c":["Battery","Ignition","Glow relay","Glow plugs 1-4"],"co":["Battery + → Relay 30","IGN 15 → Relay 86","Relay 87 → All glow plugs"],"nt":["Resistance: 0.5-2Ω"]},
    {"n":"Transmission Control","sy":"Transmission","d":"TCM, solenoids","c":["TCM","Shift sol A/B/C","Line pressure solenoid","ISS/OSS"],"co":["TCM → Sol A (Red)","TCM → Sol B (Blue)","TCM → Line pressure (Yellow)"],"nt":["Solenoid: 10-15Ω"]},
    {"n":"Petrol Fuel Injection","sy":"Fuel","d":"Injectors and pump","c":["ECU","Injectors 1-4","Fuel relay","Fuel pump"],"co":["ECU → Injector drivers","ECU → Common 12V","ECU → Relay 86","Relay 87 → Fuel pump"],"nt":["Injector: 12-16Ω"]},
    {"n":"CAN Bus Network","sy":"Network","d":"Multi-module","c":["ECM","TCM","BCM","ABS","DLC"],"co":["All: CAN-H (Yellow) twisted","All: CAN-L (Green) twisted","DLC pin 6=H, pin 14=L"],"nt":["Termination: 60Ω"]},
    {"n":"Immobilizer","sy":"Security","d":"Key transponder","c":["IMMO ECU","Antenna","Status LED","ECM"],"co":["IMMO → Antenna","IMMO → ECM (CAN)","IMMO → LED"],"nt":["Antenna: 5-20Ω"]},
]
PIDS = [
    {"p":"0100","n":"PIDs supported","d":"Bit-encoded"},{"p":"0101","n":"Monitor status","d":"MIL + readiness"},
    {"p":"0103","n":"Fuel system","d":"Open/closed loop"},{"p":"0104","n":"Engine load","d":"% of max"},
    {"p":"0105","n":"Coolant temp","d":"°C"},{"p":"010C","n":"Engine RPM","d":"((A*256)+B)/4"},
    {"p":"010D","n":"Vehicle speed","d":"km/h"},{"p":"010F","n":"Intake air temp","d":"°C"},
    {"p":"0110","n":"MAF flow rate","d":"g/s"},{"p":"0111","n":"Throttle position","d":"%"},
    {"p":"0142","n":"Module voltage","d":"V"},{"p":"0146","n":"Ambient air temp","d":"°C"},
    {"p":"015C","n":"Engine oil temp","d":"°C"},
]
VEHICLE_SPECS = [
    {"v":"Toyota Hilux 2.8 GD-6","oil":"7.5L 5W-30","coolant":"8.2L Toyota SLLC","brake":"DOT 4","trans":"ATF WS 3.5L","engine_code":"1GD-FTV","firing":"1-3-4-2","timing":"Chain"},
    {"v":"Toyota Hilux 2.4 GD-6","oil":"7.5L 5W-30","coolant":"8.0L Toyota SLLC","brake":"DOT 4","trans":"ATF WS 3.5L","engine_code":"2GD-FTV","firing":"1-3-4-2","timing":"Chain"},
    {"v":"Toyota Hilux 2.5 D-4D","oil":"6.9L 10W-40","coolant":"7.4L Toyota LLC","brake":"DOT 4","trans":"75W-90","engine_code":"2KD-FTV","firing":"1-3-4-2","timing":"Belt @150k"},
    {"v":"Ford Ranger 2.2 TDCi","oil":"6.8L 5W-30","coolant":"9.0L Motorcraft","brake":"DOT 4","trans":"ATF Mercon LV","engine_code":"P4AT","firing":"1-3-4-2","timing":"Belt @150k"},
    {"v":"VW Polo 1.4","oil":"3.8L 5W-30","coolant":"5.5L G13","brake":"DOT 4","trans":"75W-90","engine_code":"CLPA","firing":"1-3-4-2","timing":"Chain"},
    {"v":"BMW 320i (F30)","oil":"5.0L 0W-40","coolant":"7.0L BMW Blue","brake":"DOT 4","trans":"ATF ZF 8HP","engine_code":"N20B20","firing":"1-3-4-2","timing":"Chain"},
    {"v":"Mercedes C200 (W205)","oil":"6.5L 5W-40","coolant":"7.5L MB 325.0","brake":"DOT 4 Plus","trans":"ATF 7G-Tronic","engine_code":"M274","firing":"1-3-4-2","timing":"Chain"},
    {"v":"Isuzu D-Max 2.5","oil":"6.5L 15W-40","coolant":"7.8L Isuzu Blue","brake":"DOT 4","trans":"ATF Dexron III","engine_code":"4JK1-TC","firing":"1-3-4-2","timing":"Chain"},
    {"v":"Nissan NP200 1.6","oil":"4.3L 5W-40","coolant":"6.5L Nissan LLC","brake":"DOT 4","trans":"75W-80","engine_code":"K4M","firing":"1-3-4-2","timing":"Belt @100k"},
    {"v":"Hyundai i20 1.4","oil":"3.6L 5W-30","coolant":"5.3L Hyundai LLC","brake":"DOT 4","trans":"75W-85","engine_code":"G4FA","firing":"1-3-4-2","timing":"Chain"},
]
INTERVALS = [
    {"t":"Petrol Vehicle","km":15000,"months":12,"items":["Oil + oil filter","Air filter check","Spark plugs check","Brake inspection","Tyre rotation","Fluids top-up","Battery test"]},
    {"t":"Diesel Vehicle","km":10000,"months":6,"items":["Oil + oil filter","Fuel filter","Air filter","Water separator drain","Brake inspection","Glow plug check"]},
    {"t":"Truck / Heavy Diesel","km":25000,"months":6,"items":["Oil + oil filter","Fuel filter","Air dryer","Brake check","Air filter","Coolant check","Grease points"]},
    {"t":"Motorcycle","km":6000,"months":6,"items":["Oil + filter","Chain lube + adjust","Brake check","Tyre pressure","Air filter clean","Spark plug check"]},
    {"t":"Tractor / Plant","km":500,"months":3,"items":["Oil + filter (engine hours)","Hydraulic filter","Fuel filter","Air filter","Grease all points","Coolant check"]},
]
BOOK_TIMES = [
    {"job":"Oil + Filter Change (Petrol)","hrs":0.5},
    {"job":"Oil + Filter Change (Diesel)","hrs":1.0},
    {"job":"Air Filter Replace","hrs":0.3},
    {"job":"Fuel Filter Replace","hrs":0.8},
    {"job":"Spark Plugs (4-cyl)","hrs":1.0},
    {"job":"Brake Pads Front","hrs":1.5},
    {"job":"Brake Pads + Discs Front","hrs":2.5},
    {"job":"Brake Fluid Bleed","hrs":1.0},
    {"job":"Clutch Replacement","hrs":6.0},
    {"job":"Timing Belt","hrs":4.0},
    {"job":"Head Gasket","hrs":12.0},
    {"job":"Water Pump","hrs":4.0},
    {"job":"Alternator","hrs":2.0},
    {"job":"Starter Motor","hrs":2.5},
    {"job":"Radiator Replace","hrs":3.0},
    {"job":"Shock Absorber (each)","hrs":1.5},
    {"job":"Wheel Alignment","hrs":1.0},
    {"job":"Battery Replace","hrs":0.3},
    {"job":"Diagnostic Scan","hrs":0.5},
    {"job":"Full Service (Petrol)","hrs":2.0},
    {"job":"Full Service (Diesel)","hrs":2.5},
]

# ═══════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════
@app.get("/api/fault-codes")
def codes(search: str = None):
    r = list(FAULT_CODES.values())
    if search:
        q = search.lower()
        r = [c for c in r if q in c["code"].lower() or q in c["description"].lower()]
    return {"codes": r}

@app.get("/api/specs")
def specs(): return {"specs": VEHICLE_SPECS}

@app.get("/api/intervals")
def intervals(): return {"intervals": INTERVALS}

@app.get("/api/book-times")
def book_times(): return {"times": BOOK_TIMES}

@app.get("/api/torque")
def torque(): return {"bolts": TORQUE, "sequences": SEQ}

@app.get("/api/bulbs")
def bulbs(): return {"bulbs": BULBS}

@app.get("/api/batteries")
def batteries(): return {"batteries": BATTERIES}

@app.get("/api/tyres")
def tyres(): return {"tyres": TYRES}

@app.get("/api/wiring")
def wiring(): return {"circuits": WIRING}

@app.get("/api/obd-pids")
def obd_pids(): return {"pids": PIDS}

@app.get("/api/vin/{vin}")
def decode_vin(vin: str):
    v = vin.strip().upper()
    if len(v) != 17: raise HTTPException(400, "VIN must be 17 characters")
    mfr, country = WMI_DB.get(v[:3], ("Unknown", "Unknown"))
    plants = {"A":"Ingolstadt","B":"Brussels","D":"Dingolfing","F":"Flint","H":"Hiroshima","T":"Toyota City","U":"Ulsan","W":"Wolfsburg","Y":"Yokohama"}
    return {"vin":v,"manufacturer":mfr,"country":country,"year":YEAR_CODES.get(v[9],"Unknown"),"plant":plants.get(v[10],"Unknown"),"serial":v[11:]}

@app.post("/api/bolt-calc")
async def bolt_calc(r: Request):
    d = await r.json(); size = d.get("size","M8"); grade = d.get("grade","8.8"); cond = d.get("condition","dry")
    tm = {"8.8":800,"10.9":1040,"12.9":1220}; am = {"M6":20.1,"M8":36.6,"M10":58.0,"M12":84.3,"M14":115.0,"M16":157.0,"M20":245.0}; km = {"dry":0.20,"oiled":0.17,"moly":0.14}
    ts = tm.get(grade,800); a = am.get(size,36.6); k = km.get(cond,0.20)
    cf = 0.75*ts*a; dm = float(size.replace("M",""))/1000.0; nm = k*dm*cf
    return {"size":size,"grade":grade,"condition":cond,"nm":nm,"ftlb":nm*0.73756,"clamp_kn":cf/1000}

@app.post("/api/chat")
async def chat(r: Request):
    d = await r.json(); msg = d.get("message","")
    if not msg: raise HTTPException(400, "Message required")
    if not OPENAI_KEY: return {"reply":"AI not configured. Set OPENAI_API_KEY in Render."}
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        resp = c.chat.completions.create(model="gpt-3.5-turbo",
            messages=[{"role":"system","content":"You are RamsTech AI, expert mechanic."},{"role":"user","content":msg}],
            max_tokens=800, temperature=0.3)
        return {"reply": resp.choices[0].message.content}
    except Exception as e: return {"reply": f"Error: {str(e)}"}

@app.post("/api/diagnose/photo")
async def diagnose_photo(r: Request):
    d = await r.json(); img = d.get("image_base64",""); veh = d.get("vehicle_info","")
    if not img: raise HTTPException(400, "Image required")
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

@app.post("/api/paint/match")
async def match_paint(r: Request):
    d = await r.json(); img = d.get("image_base64",""); veh = d.get("vehicle_info","")
    if not img: raise HTTPException(400, "Image required")
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

@app.get("/api/stats")
def stats():
    jobs = db_list("jobs"); invs = db_list("invoices"); custs = db_list("customers"); exps = db_list("expenses")
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

@app.get("/api/analytics")
def analytics():
    jobs = db_list("jobs"); invs = db_list("invoices")
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

@app.get("/api/warranty")
def warranty_list():
    items = []
    for j in db_list("jobs"):
        if j.get("status")=="Completed" and int(j.get("warranty_months",0) or 0)>0:
            try:
                done = datetime.strptime((j.get("created") or "")[:10],"%Y-%m-%d"); months = int(j["warranty_months"])
                year = done.year + (done.month+months-1)//12; month = ((done.month+months-1)%12)+1
                expiry = done.replace(year=year,month=month); days_left = (expiry-datetime.now()).days
                items.append({"id":j["id"],"customer":j.get("customer",""),"vehicle":j.get("vehicle",""),"expiry":expiry.strftime("%Y-%m-%d"),"days_left":days_left,"status":"active" if days_left>0 else "expired"})
            except Exception: pass
    items.sort(key=lambda x:x["days_left"]); return {"warranties":items}

@app.get("/api/export/tax")
def export_tax(from_date: str = None, to_date: str = None):
    o = io.StringIO(); w = csv.writer(o)
    w.writerow(["Date","Type","Description","Customer/Note","Amount","VAT"])
    for i in db_list("invoices"):
        d = (i.get("created") or "")[:10]
        if from_date and d < from_date: continue
        if to_date and d > to_date: continue
        w.writerow([d,"INCOME",i.get("description",""),i.get("customer",""),f"{float(i.get('total',0)):.2f}",f"{float(i.get('vat',0)):.2f}"])
    for e in db_list("expenses"):
        d = e.get("date","")
        if from_date and d < from_date: continue
        if to_date and d > to_date: continue
        w.writerow([d,"EXPENSE",e.get("category",""),e.get("note",""),f"-{float(e.get('amount',0)):.2f}","0.00"])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=tax_report.csv"})

# JOBS
@app.get("/api/jobs")
def list_jobs(): return {"jobs": db_list("jobs")}

@app.post("/api/jobs")
async def create_job(r: Request):
    d = await r.json(); jid = str(uuid.uuid4())[:6]
    row = {"id":jid,"customer":d.get("customer",""),"phone":d.get("phone",""),"vehicle":d.get("vehicle",""),"registration":d.get("registration",""),"complaint":d.get("complaint",""),"assigned_to":d.get("assigned_to",""),"warranty_months":int(d.get("warranty_months",6)),"photos_before":d.get("photos_before",[]),"status":"New","created":now()}
    db_save("jobs", jid, row); return {"success":True,"job":row}

@app.put("/api/jobs/{jid}")
async def update_job(jid: str, r: Request):
    d = await r.json(); job = db_get("jobs", jid)
    if job: job["status"] = d.get("status", job["status"]); db_save("jobs", jid, job)
    return {"success":True}

@app.delete("/api/jobs/{jid}")
def delete_job(jid: str): db_del("jobs",jid); return {"success":True}

# CUSTOMERS
@app.get("/api/customers")
def list_cust(): return {"customers": db_list("customers")}

@app.post("/api/customers")
async def create_cust(r: Request):
    d = await r.json(); cid = str(uuid.uuid4())[:6]
    row = {"id":cid,"name":d.get("name",""),"phone":d.get("phone",""),"email":d.get("email",""),"created":today()}
    db_save("customers",cid,row); return {"success":True,"customer":row}

@app.delete("/api/customers/{cid}")
def delete_cust(cid: str): db_del("customers",cid); return {"success":True}

# INVOICES
@app.get("/api/invoices")
def list_inv(): return {"invoices": db_list("invoices")}

@app.post("/api/invoices")
async def create_inv(r: Request):
    d = await r.json(); labour = float(d.get("labour",0)); parts = float(d.get("parts",0))
    subtotal = labour+parts; vat = subtotal*0.15; total = subtotal+vat
    iid = str(uuid.uuid4())[:6]
    row = {"id":iid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),"description":d.get("description",""),"labour":labour,"parts":parts,"subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    db_save("invoices",iid,row); return {"success":True,"invoice":row}

@app.delete("/api/invoices/{iid}")
def delete_inv(iid: str): db_del("invoices",iid); return {"success":True}

# QUOTES
@app.get("/api/quotes")
def list_quotes(): return {"quotes": db_list("quotes")}

@app.post("/api/quotes")
async def create_quote(r: Request):
    d = await r.json(); labour = float(d.get("labour",0)); parts = float(d.get("parts",0))
    subtotal = labour+parts; vat = subtotal*0.15; total = subtotal+vat
    qid = str(uuid.uuid4())[:6]
    row = {"id":qid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),"description":d.get("description",""),"labour":labour,"parts":parts,"subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    db_save("quotes",qid,row); return {"success":True,"quote":row}

@app.post("/api/quotes/{qid}/accept")
async def accept_quote(qid: str):
    q = db_get("quotes",qid)
    if not q: raise HTTPException(404, "Not found")
    iid = str(uuid.uuid4())[:6]
    inv = {"id":iid,"customer":q["customer"],"vehicle":q["vehicle"],"description":q["description"],"labour":q["labour"],"parts":q["parts"],"subtotal":q["subtotal"],"vat":q["vat"],"total":q["total"],"created":now()}
    db_save("invoices",iid,inv); db_del("quotes",qid); return {"success":True,"invoice":inv}

@app.delete("/api/quotes/{qid}")
def delete_quote(qid: str): db_del("quotes",qid); return {"success":True}

# APPOINTMENTS
@app.get("/api/appointments")
def list_appts(): return {"appointments": db_list("appointments")}

@app.post("/api/appointments")
async def create_appt(r: Request):
    d = await r.json(); aid = str(uuid.uuid4())[:6]
    row = {"id":aid,"customer":d.get("customer",""),"phone":d.get("phone",""),"vehicle":d.get("vehicle",""),"service":d.get("service",""),"date":d.get("date",""),"time":d.get("time",""),"created":now()}
    db_save("appointments",aid,row); return {"success":True,"appointment":row}

@app.delete("/api/appointments/{aid}")
def delete_appt(aid: str): db_del("appointments",aid); return {"success":True}

# INVENTORY
@app.get("/api/inventory")
def list_inv_items(): return {"items": db_list("inventory")}

@app.get("/api/inventory/low-stock")
def low_stock():
    return {"items":[{"id":i["id"],"name":i["name"],"qty":int(i.get("qty",0)),"min":int(i.get("min_qty",5))} for i in db_list("inventory") if int(i.get("qty",0))<=int(i.get("min_qty",5))]}

@app.post("/api/inventory")
async def add_inv_item(r: Request):
    d = await r.json(); iid = str(uuid.uuid4())[:6]
    row = {"id":iid,"part_number":d.get("part_number",""),"name":d.get("name",""),"category":d.get("category",""),"qty":int(d.get("qty",0)),"min_qty":int(d.get("min_qty",5)),"cost_price":float(d.get("cost_price",0)),"sell_price":float(d.get("sell_price",0)),"supplier":d.get("supplier",""),"created":today()}
    db_save("inventory",iid,row); return {"success":True,"item":row}

@app.post("/api/inventory/{iid}/adjust")
async def adjust_inv(iid: str, r: Request):
    d = await r.json(); item = db_get("inventory",iid)
    if not item: raise HTTPException(404, "Not found")
    item["qty"] = max(0, int(item.get("qty",0))+int(d.get("delta",0)))
    db_save("inventory",iid,item); return {"success":True,"item":item}

@app.delete("/api/inventory/{iid}")
def delete_inv_item(iid: str): db_del("inventory",iid); return {"success":True}

# STAFF
@app.get("/api/staff")
def list_staff(): return {"staff": db_list("staff")}

@app.post("/api/staff")
async def add_staff(r: Request):
    d = await r.json(); sid = str(uuid.uuid4())[:6]
    row = {"id":sid,"name":d.get("name",""),"role":d.get("role",""),"phone":d.get("phone",""),"email":d.get("email",""),"hourly_rate":float(d.get("hourly_rate",150)),"created":today()}
    db_save("staff",sid,row); return {"success":True,"staff":row}

@app.delete("/api/staff/{sid}")
def delete_staff(sid: str): db_del("staff",sid); return {"success":True}

# EXPENSES
@app.get("/api/expenses")
def list_exp(): return {"expenses": db_list("expenses")}

@app.post("/api/expenses")
async def add_exp(r: Request):
    d = await r.json(); eid = str(uuid.uuid4())[:6]
    row = {"id":eid,"category":d.get("category","Other"),"amount":float(d.get("amount",0)),"date":d.get("date",today()),"note":d.get("note",""),"created":now()}
    db_save("expenses",eid,row); return {"success":True,"expense":row}

@app.delete("/api/expenses/{eid}")
def delete_exp(eid: str): db_del("expenses",eid); return {"success":True}

# SUPPLIERS
@app.get("/api/suppliers")
def list_suppliers(): return {"suppliers": db_list("suppliers")}

@app.post("/api/suppliers")
async def add_supplier(r: Request):
    d = await r.json(); sid = str(uuid.uuid4())[:6]
    row = {"id":sid,"name":d.get("name",""),"phone":d.get("phone",""),"email":d.get("email",""),"whatsapp":d.get("whatsapp",""),"category":d.get("category",""),"account_number":d.get("account_number",""),"notes":d.get("notes",""),"created":today()}
    db_save("suppliers",sid,row); return {"success":True,"supplier":row}

@app.delete("/api/suppliers/{sid}")
def delete_supplier(sid: str): db_del("suppliers",sid); return {"success":True}

# WORKSHOP
@app.get("/api/workshop")
def get_ws(): return ws_get()

@app.post("/api/workshop")
async def save_ws(r: Request):
    d = await r.json(); ws_save(d); return {"success":True,"workshop":ws_get()}

# ═══════════════════════════════════════════════
# FRONTEND HTML (with robust health check)
# ═══════════════════════════════════════════════
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="theme-color" content="#E65100">
<title>RamsTech</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#f0f2f5;--card:#fff;--text:#1a1a2e;--text2:#6b7280;--border:#e5e7eb;--primary:#E65100;--primary-light:#FFF3E0;--success:#10b981;--danger:#ef4444;--warning:#f59e0b;--info:#3b82f6;--purple:#8b5cf6;--grad1:linear-gradient(135deg,#667eea,#764ba2);--grad-success:linear-gradient(135deg,#43e97b,#38f9d7);--grad-danger:linear-gradient(135deg,#ef4444,#f87171);--grad-primary:linear-gradient(135deg,#E65100,#FF9800)}
body.dark{--bg:#0f172a;--card:#1e293b;--text:#f1f5f9;--text2:#94a3b8;--border:#334155;--primary-light:#78350f}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
html,body{overflow-x:hidden}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);padding-bottom:90px;transition:background .3s,color .3s}
.header{background:var(--grad1);color:white;padding:18px 16px 22px;text-align:center;position:relative;overflow:hidden;border-bottom-left-radius:26px;border-bottom-right-radius:26px;box-shadow:0 6px 24px rgba(102,126,234,.35)}
.header::before{content:'';position:absolute;top:-60%;right:-25%;width:320px;height:320px;background:radial-gradient(circle,rgba(255,255,255,.15),transparent 70%);border-radius:50%}
.header h1{font-size:21px;font-weight:800;display:flex;align-items:center;justify-content:center;gap:10px;position:relative;z-index:1}
.header h1 .logo{font-size:28px}
.header p{font-size:11px;opacity:.9;margin-top:4px;position:relative;z-index:1}
.top-btns{position:absolute;right:10px;top:12px;display:flex;gap:6px;z-index:2}
.top-btns button{background:rgba(255,255,255,.25);border:none;color:white;padding:8px 10px;border-radius:11px;font-size:15px;cursor:pointer}
.panel{display:none;padding:16px;max-width:820px;margin:0 auto;padding-bottom:100px}
.panel.active{display:block;animation:fadeSlide .35s ease}
@keyframes fadeSlide{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.panel-title{font-size:21px;font-weight:800;color:var(--primary);margin-bottom:18px}
.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{background:var(--card);border-radius:18px;padding:22px 12px;cursor:pointer;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border);transition:transform .15s}
.tile:active{transform:scale(.96)}
.tile-icon{font-size:38px;margin-bottom:8px;display:block}
.tile-label{font-size:12.5px;font-weight:700}
.card{background:var(--card);padding:16px;border-radius:18px;margin-bottom:12px;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border)}
.card h3{color:var(--primary);margin-bottom:10px;font-size:15px;font-weight:800}
.card p{margin:5px 0;font-size:13px;line-height:1.55}
.form-input{width:100%;padding:14px 16px;border:1.5px solid var(--border);border-radius:13px;font-size:15px;margin-bottom:10px;background:var(--card);color:var(--text);font-family:inherit}
.form-input:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 3px rgba(230,81,0,.1)}
textarea.form-input{resize:vertical;min-height:60px}
.btn{width:100%;padding:15px;border:none;border-radius:13px;font-size:15px;font-weight:800;cursor:pointer;margin-bottom:10px;background:var(--grad1);color:white;box-shadow:0 4px 14px rgba(102,126,234,.28)}
.btn:active{transform:scale(.97)}
.btn-green{background:var(--grad-success)}
.btn-dark{background:linear-gradient(135deg,#4b5563,#1f2937)}
.btn-sm{padding:8px 13px;border:none;border-radius:9px;font-size:12px;font-weight:700;cursor:pointer;margin-right:5px;margin-bottom:4px;background:var(--primary);color:white}
.btn-sm.green{background:var(--success)}.btn-sm.red{background:var(--danger)}.btn-sm.blue{background:var(--info)}.btn-sm.gray{background:#6b7280}.btn-sm.wa{background:#25D366}.btn-sm.purple{background:var(--purple)}
.badge{display:inline-block;padding:3px 10px;border-radius:7px;font-size:11px;font-weight:800;color:white;margin-left:6px}
.badge.high,.badge.critical,.badge.warn,.badge.outstanding{background:var(--danger)}
.badge.medium,.badge.inprogress{background:var(--warning)}
.badge.low,.badge.ok,.badge.completed,.badge.paid,.badge.active{background:var(--success)}
.badge.new{background:#6b7280}.badge.expired{background:#6b7280}
.list-item{padding:9px 0;border-bottom:1px solid var(--border);font-size:13px;line-height:1.5}
.list-item:last-child{border-bottom:none}
.chat-box{background:var(--card);border-radius:18px;padding:14px;height:calc(100vh - 300px);overflow-y:auto;margin-bottom:12px;border:1px solid var(--border)}
.msg{padding:12px 16px;margin:8px 0;border-radius:16px;max-width:85%;word-wrap:break-word;font-size:14px;line-height:1.5;animation:msgPop .25s ease}
@keyframes msgPop{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}
.msg.user{background:var(--grad1);color:white;margin-left:auto}
.msg.ai{background:var(--primary-light);border:1px solid var(--border)}
body.dark .msg.ai{background:#334155}
.input-row{display:flex;gap:8px;align-items:center}
.input-row input{flex:1;padding:14px 18px;border:1.5px solid var(--border);border-radius:26px;font-size:15px;outline:none;background:var(--card);color:var(--text)}
.input-row input:focus{border-color:var(--primary)}
.input-row button{padding:14px 15px;background:var(--grad1);color:white;border:none;border-radius:50%;font-weight:bold;cursor:pointer;font-size:16px}
.mic-btn{background:var(--grad-success)!important}
.mic-btn.recording{background:var(--grad-danger)!important;animation:pulse 1.2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--border);display:flex;padding:8px 4px 10px;z-index:100;box-shadow:0 -4px 20px rgba(0,0,0,.06)}
.bnav{flex:1;text-align:center;padding:6px 4px;cursor:pointer;border-radius:12px}
.bnav.active{background:var(--primary-light)}
.bnav-icon{font-size:20px;display:block;margin-bottom:3px}
.bnav-label{font-size:9px;font-weight:800;color:var(--text2);text-transform:uppercase}
.bnav.active .bnav-label{color:var(--primary)}
.status-online{background:var(--grad-success);color:white;padding:11px 16px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700;box-shadow:0 4px 12px rgba(16,185,129,.25)}
.status-offline{background:var(--grad-danger);color:white;padding:11px 16px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700;box-shadow:0 4px 12px rgba(239,68,68,.25);cursor:pointer}
.status-checking{background:#6b7280;color:white;padding:11px 16px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700}
.status-progress{background:linear-gradient(135deg,#f59e0b,#fbbf24);color:white;padding:11px 16px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700}
.empty{text-align:center;padding:40px 20px;color:var(--text2)}
.empty-icon{font-size:64px;margin-bottom:12px;display:block;opacity:.5}
.empty-title{font-size:15px;font-weight:700;color:var(--text);margin-bottom:6px}
.empty-text{font-size:13px;line-height:1.5}
.skeleton{background:linear-gradient(90deg,var(--border) 25%,rgba(255,255,255,.4) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.5s infinite;border-radius:8px}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.skeleton-card{background:var(--card);padding:16px;border-radius:18px;margin-bottom:12px;border:1px solid var(--border)}
.skeleton-line{height:12px;margin-bottom:10px;border-radius:6px}
.skeleton-line.title{width:60%;height:16px}
.skeleton-line.short{width:40%}
#toast-container{position:fixed;top:16px;left:16px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:8px;pointer-events:none}
.toast{padding:14px 18px;border-radius:14px;color:white;font-size:14px;font-weight:600;box-shadow:0 8px 24px rgba(0,0,0,.25);animation:toastIn .3s ease;max-width:500px;margin:0 auto;width:100%;display:flex;align-items:center;gap:10px}
@keyframes toastIn{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}
.toast.out{animation:toastOut .3s ease forwards}
@keyframes toastOut{to{opacity:0;transform:translateY(-20px)}}
.toast.success{background:var(--grad-success)}
.toast.error{background:var(--grad-danger)}
.toast.info{background:var(--grad1)}
.img-preview{width:100%;border-radius:16px;margin-bottom:12px}
.swatch{height:100px;border-radius:16px;border:2px solid var(--border);margin-bottom:12px}
.photo-row{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;margin-bottom:10px}
.photo-thumb{width:88px;height:88px;object-fit:cover;border-radius:12px;border:2px solid var(--border);flex-shrink:0}
.torque-table{width:100%;border-collapse:collapse;background:var(--card);border-radius:14px;overflow:hidden;font-size:12px;margin-bottom:12px}
.torque-table th{background:var(--grad1);color:white;padding:11px 9px;text-align:left;font-weight:700;font-size:11px}
.torque-table td{padding:11px 9px;border-bottom:1px solid var(--border)}
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat-card{background:var(--card);padding:16px 12px;border-radius:18px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border);position:relative;overflow:hidden}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--grad-primary)}
.stat-card.blue::before{background:linear-gradient(90deg,#3b82f6,#60a5fa)}
.stat-card.green::before{background:var(--grad-success)}
.stat-card.red::before{background:var(--grad-danger)}
.stat-card.purple::before{background:linear-gradient(90deg,#8b5cf6,#a78bfa)}
.stat-card .num{font-size:23px;font-weight:800;color:var(--primary);line-height:1.2}
.stat-card.blue .num{color:var(--info)}
.stat-card.green .num{color:var(--success)}
.stat-card.red .num{color:var(--danger)}
.stat-card.purple .num{color:var(--purple)}
.stat-card .lbl{font-size:10px;color:var(--text2);margin-top:5px;font-weight:700;text-transform:uppercase}
canvas{max-height:220px}
@media print{.header,.bottom-nav,.no-print,button,.btn,.btn-sm,#toast-container{display:none!important}.panel{display:block!important;padding:0}.panel:not(.active){display:none!important}body{background:white;color:black;padding:0}.card{box-shadow:none;border:1px solid #ccc}}
</style>
</head>
<body>

<div id="toast-container"></div>

<div class="header">
<h1><span class="logo" id="logoDisplay">🔧</span> <span id="wsName">RAMSTECH</span></h1>
<p id="wsSub">AI Workshop Assistant</p>
<div class="top-btns">
<button onclick="toggleTheme()" id="themeBtn">🌙</button>
</div>
</div>

<div id="home" class="panel active">
<div class="card">
  <div id="status"><span class="status-checking">Checking backend...</span></div>
  <div id="statusDetail" style="margin-top:8px;font-size:12px;color:var(--text2)"></div>
</div>
<div class="tile-grid" id="homeGrid"></div>
</div>

<div id="dashboard" class="panel"><div class="panel-title">📊 Dashboard</div><div id="dashStats"></div><div class="card"><h3>💰 Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div><div class="card"><h3>📋 Job Status</h3><canvas id="jobChart"></canvas></div><div class="card"><h3>⚠️ Low Stock</h3><div id="dashLowStock"></div></div></div>
<div id="analytics" class="panel"><div class="panel-title">📈 Analytics</div><div id="analyticsContent"></div></div>
<div id="warranty" class="panel"><div class="panel-title">🎁 Warranty</div><div id="warrantyList"></div></div>
<div id="tax" class="panel"><div class="panel-title">🧾 Tax Report</div><div class="card"><input class="form-input" id="taxFrom" type="date"><input class="form-input" id="taxTo" type="date"><button class="btn btn-dark" onclick="downloadTax()">📥 Download CSV</button></div></div>
<div id="vin" class="panel"><div class="panel-title">🔍 VIN Decoder</div><div class="card"><input class="form-input" id="vinInput" placeholder="17-char VIN" maxlength="17" style="text-transform:uppercase"><button class="btn btn-green" onclick="decodeVin()">🔍 Decode</button><div id="vinResult"></div></div></div>
<div id="photo" class="panel"><div class="panel-title">📸 Photo Diag</div><div class="card"><input class="form-input" id="photoVehicle" placeholder="Vehicle info"><input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)"><div id="photoPreview"></div><button class="btn btn-green" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze</button><div id="photoResult"></div></div></div>
<div id="paint" class="panel"><div class="panel-title">🎨 Paint Match</div><div class="card"><input class="form-input" id="paintVehicle" placeholder="Vehicle info"><input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)"><div id="paintPreview"></div><button class="btn btn-green" id="paintBtn" onclick="matchPaint()">🎨 Match</button><div id="paintResult"></div></div></div>
<div id="specs" class="panel"><div class="panel-title">🔧 Vehicle Specs</div><input type="text" class="form-input" id="specsSearch" placeholder="🔍 Search..." oninput="filterSpecs()"><div id="specsList"></div></div>
<div id="intervals" class="panel"><div class="panel-title">⏰ Service Intervals</div><input type="text" class="form-input" id="intervalSearch" placeholder="🔍 Search..." oninput="filterIntervals()"><div id="intervalList"></div></div>
<div id="booktime" class="panel"><div class="panel-title">⏱️ Book Time</div><input type="text" class="form-input" id="bookSearch" placeholder="🔍 Search job..." oninput="filterBook()"><div id="bookList"></div></div>
<div id="suppliers" class="panel"><div class="panel-title">📞 Suppliers</div><button class="btn btn-green" onclick="showForm('supplierForm')">+ Add Supplier</button><div id="supplierForm" style="display:none"><div class="card"><input class="form-input" id="supName" placeholder="Supplier name"><input class="form-input" id="supPhone" placeholder="Phone"><input class="form-input" id="supEmail" placeholder="Email"><input class="form-input" id="supWhatsapp" placeholder="WhatsApp"><input class="form-input" id="supCategory" placeholder="Category"><input class="form-input" id="supAccount" placeholder="Account #"><textarea class="form-input" id="supNotes" placeholder="Notes" rows="2"></textarea><button class="btn btn-green" onclick="addSupplier()">Save</button><button class="btn btn-dark" onclick="hideForm('supplierForm')">Cancel</button></div></div><div id="supplierList"></div></div>
<div id="chat" class="panel"><div class="panel-title">🤖 AI Chat</div><div class="chat-box" id="chatBox"><div class="msg ai">Hi! Ask about vehicle repairs.</div></div><div class="input-row"><input type="text" id="chatInput" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendMsg()"><button class="mic-btn" id="micBtn" onclick="toggleMic()">🎤</button><button onclick="sendMsg()">➤</button></div></div>
<div id="codes" class="panel"><div class="panel-title">📟 Fault Codes</div><input type="text" class="form-input" id="codeSearch" placeholder="🔍 Search code..." oninput="searchCodes()"><div id="codeResults"></div></div>
<div id="jobs" class="panel"><div class="panel-title">📋 Jobs</div><button class="btn btn-green" onclick="showForm('jobForm')">+ New Job</button><div id="jobForm" style="display:none"><div class="card"><input class="form-input" id="jCustomer" placeholder="Customer"><input class="form-input" id="jPhone" placeholder="Phone"><input class="form-input" id="jVehicle" placeholder="Vehicle"><input class="form-input" id="jReg" placeholder="Registration"><textarea class="form-input" id="jComplaint" placeholder="Complaint" rows="2"></textarea><select class="form-input" id="jAssigned"><option value="">— Assign staff —</option></select><input class="form-input" id="jWarranty" type="number" placeholder="Warranty months" value="6"><label style="font-size:13px;font-weight:700;display:block;margin-bottom:6px">📸 Before Photos</label><input type="file" id="jBefore" accept="image/*" multiple capture="environment" class="form-input" onchange="addPhoto(event)"><div class="photo-row" id="beforeRow"></div><button class="btn btn-green" onclick="createJob()">Save</button><button class="btn btn-dark" onclick="hideForm('jobForm')">Cancel</button></div></div><div id="jobList"></div></div>
<div id="quotes" class="panel"><div class="panel-title">💬 Quotes</div><button class="btn btn-green" onclick="showForm('quoteForm')">+ New Quote</button><div id="quoteForm" style="display:none"><div class="card"><input class="form-input" id="qCustomer" placeholder="Customer"><input class="form-input" id="qVehicle" placeholder="Vehicle"><textarea class="form-input" id="qDesc" placeholder="Work description" rows="2"></textarea><select class="form-input" id="qBookTime" onchange="applyBookTime('q')"><option value="">— Auto labour —</option></select><input class="form-input" id="qLabour" type="number" placeholder="Labour R" value="0"><input class="form-input" id="qParts" type="number" placeholder="Parts R" value="0"><button class="btn btn-green" onclick="createQuote()">Save</button><button class="btn btn-dark" onclick="hideForm('quoteForm')">Cancel</button></div></div><div id="quoteList"></div></div>
<div id="appointments" class="panel"><div class="panel-title">📅 Appointments</div><button class="btn btn-green" onclick="showForm('apptForm')">+ New Appt</button><div id="apptForm" style="display:none"><div class="card"><input class="form-input" id="aCustomer" placeholder="Customer"><input class="form-input" id="aPhone" placeholder="Phone"><input class="form-input" id="aVehicle" placeholder="Vehicle"><input class="form-input" id="aService" placeholder="Service"><input class="form-input" id="aDate" type="date"><input class="form-input" id="aTime" type="time"><button class="btn btn-green" onclick="createAppt()">Book</button><button class="btn btn-dark" onclick="hideForm('apptForm')">Cancel</button></div></div><div id="apptList"></div></div>
<div id="customers" class="panel"><div class="panel-title">👥 Customers</div><button class="btn btn-green" onclick="showForm('custForm')">+ New Customer</button><div id="custForm" style="display:none"><div class="card"><input class="form-input" id="cName" placeholder="Name"><input class="form-input" id="cPhone" placeholder="Phone"><input class="form-input" id="cEmail" placeholder="Email"><button class="btn btn-green" onclick="createCustomer()">Save</button><button class="btn btn-dark" onclick="hideForm('custForm')">Cancel</button></div></div><div id="custList"></div></div>
<div id="invoices" class="panel"><div class="panel-title">💰 Invoices</div><button class="btn btn-green" onclick="showForm('invForm')">+ New Invoice</button><div id="invForm" style="display:none"><div class="card"><input class="form-input" id="iCustomer" placeholder="Customer"><input class="form-input" id="iVehicle" placeholder="Vehicle"><input class="form-input" id="iDesc" placeholder="Description"><select class="form-input" id="iBookTime" onchange="applyBookTime('i')"><option value="">— Auto labour —</option></select><input class="form-input" id="iLabour" type="number" placeholder="Labour R"><input class="form-input" id="iParts" type="number" placeholder="Parts R"><button class="btn btn-green" onclick="createInvoice()">Save</button><button class="btn btn-dark" onclick="hideForm('invForm')">Cancel</button></div></div><div id="invList"></div></div>
<div id="inventory" class="panel"><div class="panel-title">📦 Inventory</div><button class="btn btn-green" onclick="showForm('invItemForm')">+ Add Item</button><div id="invItemForm" style="display:none"><div class="card"><input class="form-input" id="pNumber" placeholder="Part #"><input class="form-input" id="pName" placeholder="Name"><input class="form-input" id="pCategory" placeholder="Category"><input class="form-input" id="pQty" type="number" placeholder="Qty"><input class="form-input" id="pMinQty" type="number" placeholder="Min qty" value="5"><input class="form-input" id="pCost" type="number" placeholder="Cost R"><input class="form-input" id="pSell" type="number" placeholder="Sell R"><input class="form-input" id="pSupplier" placeholder="Supplier"><button class="btn btn-green" onclick="addInventory()">Save</button><button class="btn btn-dark" onclick="hideForm('invItemForm')">Cancel</button></div></div><div id="inventoryList"></div></div>
<div id="staff" class="panel"><div class="panel-title">👷 Staff</div><button class="btn btn-green" onclick="showForm('staffForm')">+ Add Staff</button><div id="staffForm" style="display:none"><div class="card"><input class="form-input" id="stName" placeholder="Name"><input class="form-input" id="stRole" placeholder="Role"><input class="form-input" id="stPhone" placeholder="Phone"><input class="form-input" id="stEmail" placeholder="Email"><input class="form-input" id="stRate" type="number" placeholder="Hourly rate R" value="150"><button class="btn btn-green" onclick="addStaff()">Save</button><button class="btn btn-dark" onclick="hideForm('staffForm')">Cancel</button></div></div><div id="staffList"></div></div>
<div id="expenses" class="panel"><div class="panel-title">💸 Expenses</div><button class="btn btn-green" onclick="showForm('expForm')">+ Add Expense</button><div id="expForm" style="display:none"><div class="card"><select class="form-input" id="exCat"><option>Rent</option><option>Utilities</option><option>Tools</option><option>Parts</option><option>Salaries</option><option>Fuel</option><option>Marketing</option><option>Other</option></select><input class="form-input" id="exAmount" type="number" placeholder="Amount R"><input class="form-input" id="exDate" type="date"><textarea class="form-input" id="exNote" placeholder="Note" rows="2"></textarea><button class="btn btn-green" onclick="addExpense()">Save</button><button class="btn btn-dark" onclick="hideForm('expForm')">Cancel</button></div></div><div id="expenseList"></div></div>
<div id="torque" class="panel"><div class="panel-title">⚙️ Torque Specs</div><input type="text" class="form-input" id="torqueSearch" placeholder="🔍 Search..." oninput="filterTorque()"><h3 style="margin:8px 0;font-size:14px;color:var(--text2)">Bolt Torque</h3><div id="torqueTable"></div><h3 style="margin:16px 0 8px;font-size:14px;color:var(--text2)">Sequences</h3><div id="torqueSeq"></div></div>
<div id="boltcalc" class="panel"><div class="panel-title">🔧 Bolt Calculator</div><div class="card"><select class="form-input" id="boltSize"><option>M6</option><option>M8</option><option selected>M10</option><option>M12</option><option>M14</option><option>M16</option><option>M20</option></select><select class="form-input" id="boltGrade"><option>8.8</option><option selected>10.9</option><option>12.9</option></select><select class="form-input" id="boltCondition"><option value="dry">Dry</option><option value="oiled">Lightly oiled</option><option value="moly">Moly</option></select><button class="btn" onclick="calcTorque()">Calculate</button><div id="boltResult"></div></div></div>
<div id="bulbs" class="panel"><div class="panel-title">💡 Bulbs</div><input type="text" class="form-input" id="bulbSearch" placeholder="🔍 Search..." oninput="filterBulbs()"><div id="bulbList"></div></div>
<div id="batteries" class="panel"><div class="panel-title">🔋 Batteries</div><input type="text" class="form-input" id="battSearch" placeholder="🔍 Search..." oninput="filterBatt()"><div id="battList"></div></div>
<div id="tyres" class="panel"><div class="panel-title">🛞 Tyres</div><input type="text" class="form-input" id="tyreSearch" placeholder="🔍 Search..." oninput="filterTyre()"><div id="tyreList"></div></div>
<div id="wiring" class="panel"><div class="panel-title">🔌 Wiring</div><input type="text" class="form-input" id="wiringSearch" placeholder="🔍 Search..." oninput="filterWiring()"><div id="wiringList"></div></div>
<div id="obd" class="panel"><div class="panel-title">⚡ OBD-II</div><input type="text" class="form-input" id="obdSearch" placeholder="🔍 Search..." oninput="filterOBD()"><div id="obdList"></div></div>
<div id="settings" class="panel"><div class="panel-title">⚙️ Settings</div><div class="card"><h3>🏢 Workshop</h3><input class="form-input" id="sLogo" placeholder="🔧" maxlength="4"><input class="form-input" id="sName" placeholder="Workshop name"><input class="form-input" id="sPhone" placeholder="Phone"><input class="form-input" id="sEmail" placeholder="Email"><input class="form-input" id="sAddress" placeholder="Address"><input class="form-input" id="sHours" placeholder="Trading hours"><input class="form-input" id="sRate" type="number" placeholder="Labour rate R/hr"><h3 style="margin-top:16px">🧾 Business</h3><input class="form-input" id="sVat" placeholder="VAT number"><input class="form-input" id="sCompany" placeholder="Company reg"><input class="form-input" id="sBank" placeholder="Bank details"><h3 style="margin-top:16px">📜 Terms</h3><textarea class="form-input" id="sTerms" rows="5"></textarea><button class="btn btn-green" onclick="saveSettings()">Save</button></div></div>

<div class="bottom-nav no-print">
<div class="bnav active" onclick="showTab('home',this)"><div class="bnav-icon">🏠</div><div class="bnav-label">Home</div></div>
<div class="bnav" onclick="showTab('chat',this)"><div class="bnav-icon">🤖</div><div class="bnav-label">AI</div></div>
<div class="bnav" onclick="showTab('jobs',this)"><div class="bnav-icon">📋</div><div class="bnav-label">Jobs</div></div>
<div class="bnav" onclick="showTab('specs',this)"><div class="bnav-icon">🔧</div><div class="bnav-label">Specs</div></div>
<div class="bnav" onclick="showTab('settings',this)"><div class="bnav-icon">⚙️</div><div class="bnav-label">More</div></div>
</div>

<script>
// ═══ TOAST ═══
function toast(msg, type='info', dur=3000){
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  const icons = {success:'✓', error:'✕', info:'ℹ', warning:'⚠'};
  t.innerHTML = '<span style="font-size:20px">' + icons[type] + '</span><span>' + msg + '</span>';
  c.appendChild(t);
  setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 300); }, dur);
}

// ═══ HELPERS ═══
function showForm(id){document.getElementById(id).style.display='block';}
function hideForm(id){document.getElementById(id).style.display='none';}
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML;}
async function jget(u){const r=await fetch(u);return r.json();}
async function jpost(u,b){const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json();}
async function jput(u,b){const r=await fetch(u,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json();}
function emptyState(icon, title, text){
  return '<div class="empty"><span class="empty-icon">' + icon + '</span><div class="empty-title">' + title + '</div><div class="empty-text">' + text + '</div></div>';
}
function skeleton(){
  return '<div class="skeleton-card"><div class="skeleton skeleton-line title"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div></div>';
}

// ═══ ROBUST HEALTH CHECK — WAITS UP TO 60s, 3 RETRIES ═══
async function checkStatus(){
  const statusEl = document.getElementById('status');
  const detailEl = document.getElementById('statusDetail');
  const MAX_ATTEMPTS = 3;
  const TIMEOUT_MS = 60000;
  
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++){
    statusEl.innerHTML = '<span class="status-progress">⏳ Waking backend... attempt ' + attempt + ' of ' + MAX_ATTEMPTS + '</span>';
    detailEl.textContent = 'Render free tier sleeps after 15 min. First request can take up to 60 seconds. Please wait...';
    
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
      const start = Date.now();
      
      const r = await fetch('/health', { signal: controller.signal, cache: 'no-store' });
      clearTimeout(timer);
      
      if (r.ok){
        const elapsed = Math.round((Date.now() - start) / 1000);
        statusEl.innerHTML = '<span class="status-online">✓ Backend Online (' + elapsed + 's)</span>';
        detailEl.textContent = '';
        return true;
      }
    } catch(e){
      // try again
    }
    
    if (attempt < MAX_ATTEMPTS){
      statusEl.innerHTML = '<span class="status-progress">🔄 Retrying... (' + attempt + '/' + MAX_ATTEMPTS + ')</span>';
      await new Promise(r => setTimeout(r, 2000));
    }
  }
  
  statusEl.innerHTML = '<span class="status-offline">✗ Backend Offline — Tap to Retry</span>';
  detailEl.textContent = 'Backend may still be waking up. Tap the red button to try again.';
  statusEl.onclick = () => checkStatus();
  return false;
}

// ═══ HOME TILES ═══
const TILES = [
  ['dashboard','📊','Dashboard'],['chat','🤖','AI Chat'],['codes','📟','Fault Codes'],
  ['vin','🔍','VIN'],['photo','📸','Photo Diag'],['paint','🎨','Paint'],
  ['specs','🔧','Vehicle Specs'],['intervals','⏰','Intervals'],['booktime','⏱️','Book Time'],
  ['suppliers','📞','Suppliers'],['jobs','📋','Jobs'],['quotes','💬','Quotes'],
  ['appointments','📅','Appts'],['customers','👥','Customers'],['invoices','💰','Invoices'],
  ['inventory','📦','Inventory'],['staff','👷','Staff'],['expenses','💸','Expenses'],
  ['analytics','📈','Analytics'],['warranty','🎁','Warranty'],['tax','🧾','Tax'],
  ['torque','⚙️','Torque'],['boltcalc','🔧','Bolt Calc'],['bulbs','💡','Bulbs'],
  ['batteries','🔋','Batteries'],['tyres','🛞','Tyres'],['wiring','🔌','Wiring'],
  ['obd','⚡','OBD-II'],['settings','⚙️','Settings']
];
document.getElementById('homeGrid').innerHTML = TILES.map(t =>
  '<div class="tile" onclick="showTab(\'' + t[0] + '\')"><span class="tile-icon">' + t[1] + '</span><div class="tile-label">' + t[2] + '</div></div>'
).join('');

// ═══ TAB SWITCHING ═══
function showTab(name, el){
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.bnav').forEach(t => t.classList.remove('active'));
  const panel = document.getElementById(name);
  if (panel) panel.classList.add('active');
  if (el && el.classList) el.classList.add('active');
  window.scrollTo(0,0);
  const loaders = {
    dashboard: loadDash, analytics: loadAnalytics, warranty: loadWarranty, tax: loadTax,
    specs: loadSpecs, intervals: loadIntervals, booktime: loadBookTime, suppliers: loadSuppliers,
    jobs: () => { loadJobs(); loadStaffDropdown(); loadBookTimes(); },
    quotes: () => { loadQuotes(); loadBookTimes(); },
    appointments: loadAppts, customers: loadCust,
    invoices: () => { loadInv(); loadBookTimes(); },
    inventory: loadInventory, staff: loadStaff, expenses: loadExpenses,
    torque: loadTorque, bulbs: loadBulbs, batteries: loadBatt, tyres: loadTyre,
    wiring: loadWiring, obd: loadOBD, settings: loadSettings,
    codes: () => { if (!document.getElementById('codeResults').dataset.loaded) searchCodes(); }
  };
  if (loaders[name]) try { loaders[name](); } catch(e) { console.error(e); }
}

// ═══ THEME ═══
function toggleTheme(){
  document.body.classList.toggle('dark');
  const d = document.body.classList.contains('dark');
  localStorage.setItem('theme', d ? 'dark' : 'light');
  document.getElementById('themeBtn').textContent = d ? '☀️' : '🌙';
}
if (localStorage.getItem('theme') === 'dark'){
  document.body.classList.add('dark');
  document.getElementById('themeBtn').textContent = '☀️';
}

// ═══ IMAGE ═══
function compressImage(file, mw, q){
  return new Promise(res => {
    const r = new FileReader();
    r.onload = e => {
      const img = new Image();
      img.onload = () => {
        const c = document.createElement('canvas');
        let { width, height } = img;
        if (width > mw){ height = (height * mw) / width; width = mw; }
        c.width = width; c.height = height;
        c.getContext('2d').drawImage(img, 0, 0, width, height);
        res(c.toDataURL('image/jpeg', q));
      };
      img.src = e.target.result;
    };
    r.readAsDataURL(file);
  });
}

// Start health check on page load
checkStatus();

// ═══ CHAT ═══
let rec = null, isRec = false;
function toggleMic(){
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)){ toast('Voice not supported', 'warning'); return; }
  if (!rec){
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    rec = new SR(); rec.lang = 'en-ZA';
    rec.onresult = e => { document.getElementById('chatInput').value = e.results[0][0].transcript; resetMic(); sendMsg(); };
    rec.onerror = resetMic; rec.onend = resetMic;
  }
  function resetMic(){ isRec = false; document.getElementById('micBtn').classList.remove('recording'); document.getElementById('micBtn').textContent = '🎤'; }
  if (isRec){ rec.stop(); resetMic(); }
  else { try { rec.start(); isRec = true; document.getElementById('micBtn').classList.add('recording'); document.getElementById('micBtn').textContent = '⏹'; } catch(e){ toast(e.message, 'error'); } }
}
async function sendMsg(){
  const i = document.getElementById('chatInput');
  const m = i.value.trim(); if (!m) return;
  const b = document.getElementById('chatBox');
  b.innerHTML += '<div class="msg user">' + esc(m) + '</div>';
  i.value = ''; b.scrollTop = b.scrollHeight;
  b.innerHTML += '<div class="msg ai" id="typ">Thinking...</div>';
  b.scrollTop = b.scrollHeight;
  try {
    const d = await jpost('/api/chat', {message:m});
    document.getElementById('typ').outerHTML = '<div class="msg ai">' + esc(d.reply) + '</div>';
  } catch(e){ document.getElementById('typ').outerHTML = '<div class="msg ai">Error</div>'; }
  b.scrollTop = b.scrollHeight;
}

// ═══ DASHBOARD ═══
let rC = null, jC = null;
async function loadDash(){
  try {
    const d = await jget('/api/stats');
    document.getElementById('dashStats').innerHTML =
      '<div class="stats-row">' +
      '<div class="stat-card blue"><div class="num">' + d.jobs_total + '</div><div class="lbl">Jobs</div></div>' +
      '<div class="stat-card purple"><div class="num">' + d.jobs_open + '</div><div class="lbl">Open</div></div>' +
      '<div class="stat-card green"><div class="num">' + d.jobs_completed + '</div><div class="lbl">Done</div></div>' +
      '<div class="stat-card"><div class="num">' + d.customers + '</div><div class="lbl">Customers</div></div>' +
      '<div class="stat-card green"><div class="num">R' + d.revenue + '</div><div class="lbl">Revenue</div></div>' +
      '<div class="stat-card red"><div class="num">R' + d.expenses + '</div><div class="lbl">Expenses</div></div>' +
      '</div>';
    if (rC) rC.destroy();
    const c1 = document.getElementById('revenueChart');
    if (c1) rC = new Chart(c1, {type:'line', data:{labels:d.revenue_labels, datasets:[{data:d.revenue_data, borderColor:'#667eea', backgroundColor:'rgba(102,126,234,.15)', tension:.4, fill:true, borderWidth:3}]}, options:{responsive:true, plugins:{legend:{display:false}}}});
    if (jC) jC.destroy();
    const c2 = document.getElementById('jobChart');
    if (c2) jC = new Chart(c2, {type:'doughnut', data:{labels:['New','Progress','Done'], datasets:[{data:[d.jobs_new, d.jobs_progress, d.jobs_completed], backgroundColor:['#6b7280','#f59e0b','#10b981'], borderWidth:0}]}, options:{responsive:true, plugins:{legend:{position:'bottom'}}}});
    const ls = await jget('/api/inventory/low-stock');
    document.getElementById('dashLowStock').innerHTML = ls.items.length ? ls.items.map(i => '<div class="list-item">⚠️ <strong>' + esc(i.name) + '</strong> — ' + i.qty + ' left</div>').join('') : '<p style="color:var(--text2)">✓ All stock OK</p>';
  } catch(e){ toast('Failed to load dashboard', 'error'); }
}

// ═══ ANALYTICS ═══
async function loadAnalytics(){
  try {
    const d = await jget('/api/analytics');
    let h = '<div class="stats-row">' +
      '<div class="stat-card blue"><div class="num">R' + d.avg_invoice.toFixed(0) + '</div><div class="lbl">Avg Invoice</div></div>' +
      '<div class="stat-card green"><div class="num">R' + d.total_revenue.toFixed(0) + '</div><div class="lbl">Revenue</div></div>' +
      '<div class="stat-card purple"><div class="num">' + d.invoices_count + '</div><div class="lbl">Invoices</div></div>' +
      '<div class="stat-card"><div class="num">' + d.jobs_count + '</div><div class="lbl">Jobs</div></div>' +
      '</div>';
    if (d.top_services.length){
      h += '<div class="card"><h3>🔥 Top Jobs</h3>';
      d.top_services.forEach(s => { h += '<div class="list-item"><strong>' + esc(s.name) + '</strong> <span style="float:right;color:var(--text2)">' + s.count + '×</span></div>'; });
      h += '</div>';
    }
    if (d.top_customers.length){
      h += '<div class="card"><h3>⭐ Top Customers</h3>';
      d.top_customers.forEach(x => { h += '<div class="list-item"><strong>' + esc(x.name) + '</strong> <span style="float:right;color:var(--success)">R' + x.total.toFixed(0) + '</span></div>'; });
      h += '</div>';
    }
    document.getElementById('analyticsContent').innerHTML = h;
  } catch(e){ toast('Failed to load analytics', 'error'); }
}

// ═══ WARRANTY ═══
async function loadWarranty(){
  const c = document.getElementById('warrantyList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/warranty');
    c.innerHTML = d.warranties.length
      ? d.warranties.map(w => {
          const cls = w.status === 'active' ? 'active' : 'expired';
          return '<div class="card"><h3>🎁 ' + esc(w.vehicle) + ' <span class="badge ' + cls + '">' + w.status.toUpperCase() + '</span></h3>' +
            '<p><strong>' + esc(w.customer) + '</strong></p>' +
            '<div class="list-item">Expires: <strong>' + esc(w.expiry) + '</strong></div>' +
            '<div class="list-item">' + (w.days_left > 0 ? '<span style="color:var(--success);font-weight:700">' + w.days_left + ' days remaining</span>' : '<span style="color:var(--danger)">Expired</span>') + '</div></div>';
        }).join('')
      : emptyState('🎁','No active warranties','Complete a job with warranty to see it here.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load warranties.'); }
}

// ═══ TAX ═══
async function loadTax(){
  const n = new Date();
  const f = new Date(n.getFullYear(), n.getMonth(), 1);
  document.getElementById('taxFrom').value = f.toISOString().slice(0,10);
  document.getElementById('taxTo').value = n.toISOString().slice(0,10);
}
function downloadTax(){
  const f = document.getElementById('taxFrom').value;
  const t = document.getElementById('taxTo').value;
  if (!f || !t){ toast('Select both dates', 'warning'); return; }
  window.location.href = '/api/export/tax?from_date=' + f + '&to_date=' + t;
  toast('Download started', 'success');
}

// ═══ VIN ═══
async function decodeVin(){
  const vin = document.getElementById('vinInput').value.trim().toUpperCase();
  const c = document.getElementById('vinResult');
  if (vin.length !== 17){ toast('VIN must be 17 characters', 'warning'); return; }
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/vin/' + vin);
    if (d.detail){ c.innerHTML = ''; toast(d.detail, 'error'); return; }
    c.innerHTML = '<div class="card"><h3>🔍 Vehicle Info</h3>' +
      '<div class="list-item"><strong>VIN:</strong> ' + d.vin + '</div>' +
      '<div class="list-item"><strong>Manufacturer:</strong> ' + d.manufacturer + '</div>' +
      '<div class="list-item"><strong>Country:</strong> ' + d.country + '</div>' +
      '<div class="list-item"><strong>Year:</strong> ' + d.year + '</div>' +
      '<div class="list-item"><strong>Plant:</strong> ' + d.plant + '</div></div>';
  } catch(e){ c.innerHTML = ''; toast('Failed', 'error'); }
}

// ═══ PHOTO DIAG ═══
let diagB64 = '';
async function previewDiag(e){ const f = e.target.files[0]; if (!f) return; diagB64 = await compressImage(f, 1200, 0.75); document.getElementById('photoPreview').innerHTML = '<img class="img-preview" src="' + diagB64 + '">'; }
async function diagnosePhoto(){
  const btn = document.getElementById('photoBtn');
  const c = document.getElementById('photoResult');
  if (!diagB64){ toast('Select a photo first', 'warning'); return; }
  btn.disabled = true; btn.innerHTML = '📸 Analyzing...';
  c.innerHTML = skeleton();
  try {
    const d = await jpost('/api/diagnose/photo', {image_base64:diagB64, vehicle_info:document.getElementById('photoVehicle').value});
    if (!d.success){ c.innerHTML = ''; toast(d.error || 'Failed', 'error'); }
    else {
      let h = '<div class="card"><h3>🔍 ' + esc(d.problem || 'Detected') + '</h3><p><strong>Confidence:</strong> ' + (d.confidence || '?') + '</p>' + (d.description ? '<p>' + esc(d.description) + '</p>' : '') + '</div>';
      if (d.possible_causes && d.possible_causes.length) h += '<div class="card"><h3>Causes</h3>' + d.possible_causes.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '</div>';
      if (d.diagnostic_steps && d.diagnostic_steps.length) h += '<div class="card"><h3>Steps</h3>' + d.diagnostic_steps.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '</div>';
      if (d.safety_warnings && d.safety_warnings.length) h += '<div class="card" style="background:#fef2f2;border-color:#fecaca"><h3 style="color:var(--danger)">⚠️ Safety</h3>' + d.safety_warnings.map(x => '<div class="list-item">⚠ ' + esc(x) + '</div>').join('') + '</div>';
      c.innerHTML = h;
      toast('Analysis complete', 'success');
    }
  } catch(e){ c.innerHTML = ''; toast('Error', 'error'); }
  btn.disabled = false; btn.innerHTML = '📸 Analyze';
}

// ═══ PAINT ═══
let paintB64 = '';
async function previewPaint(e){ const f = e.target.files[0]; if (!f) return; paintB64 = await compressImage(f, 1200, 0.75); document.getElementById('paintPreview').innerHTML = '<img class="img-preview" src="' + paintB64 + '">'; }
async function matchPaint(){
  const btn = document.getElementById('paintBtn');
  const c = document.getElementById('paintResult');
  if (!paintB64){ toast('Select a photo first', 'warning'); return; }
  btn.disabled = true; btn.innerHTML = '🎨 Analyzing...';
  c.innerHTML = skeleton();
  try {
    const d = await jpost('/api/paint/match', {image_base64:paintB64, vehicle_info:document.getElementById('paintVehicle').value});
    if (!d.success){ c.innerHTML = ''; toast(d.error || 'Failed', 'error'); }
    else {
      const col = d.detected_colour || {};
      let h = '<div class="card"><div class="swatch" style="background:' + (col.hex_code || '#ccc') + '"></div><h3>' + esc(col.name || 'Unknown') + '</h3><p><strong>' + esc(col.finish || '') + '</strong>' + (col.colour_family ? ' • ' + esc(col.colour_family) : '') + '</p><p style="font-family:monospace">' + (col.hex_code || '') + '</p><p>Confidence: <strong>' + (d.confidence || '?') + '</strong></p></div>';
      if (d.brand_codes && d.brand_codes.length){ h += '<div class="card"><h3>Brand Codes</h3>'; d.brand_codes.forEach(b => { h += '<div class="list-item"><strong>' + esc(b.brand) + ':</strong> ' + esc(b.code || '?') + '</div>'; }); h += '</div>'; }
      c.innerHTML = h;
      toast('Match found', 'success');
    }
  } catch(e){ c.innerHTML = ''; toast('Error', 'error'); }
  btn.disabled = false; btn.innerHTML = '🎨 Match';
}

// ═══ SPECS ═══
let specsData = [];
async function loadSpecs(){ if (!specsData.length){ try { specsData = (await jget('/api/specs')).specs; } catch(e){ return; } } filterSpecs(); }
function filterSpecs(){
  const q = (document.getElementById('specsSearch').value || '').toLowerCase();
  const f = specsData.filter(x => !q || x.v.toLowerCase().includes(q));
  document.getElementById('specsList').innerHTML = f.length ? f.map(s => '<div class="card"><h3>🔧 ' + esc(s.v) + '</h3><div class="list-item"><strong>Engine:</strong> ' + esc(s.engine_code) + '</div><div class="list-item"><strong>Oil:</strong> ' + esc(s.oil) + '</div><div class="list-item"><strong>Coolant:</strong> ' + esc(s.coolant) + '</div><div class="list-item"><strong>Brake:</strong> ' + esc(s.brake) + '</div><div class="list-item"><strong>Trans:</strong> ' + esc(s.trans) + '</div><div class="list-item"><strong>Firing:</strong> ' + esc(s.firing) + '</div><div class="list-item"><strong>Timing:</strong> ' + esc(s.timing) + '</div></div>').join('') : emptyState('🔧','No match','');
}

// ═══ INTERVALS ═══
let intData = [];
async function loadIntervals(){ if (!intData.length){ try { intData = (await jget('/api/intervals')).intervals; } catch(e){ return; } } filterIntervals(); }
function filterIntervals(){
  const q = (document.getElementById('intervalSearch').value || '').toLowerCase();
  const f = intData.filter(x => !q || x.t.toLowerCase().includes(q));
  document.getElementById('intervalList').innerHTML = f.map(s => '<div class="card"><h3>⏰ ' + esc(s.t) + '</h3><div class="list-item"><strong>Every:</strong> ' + s.km + ' km / ' + s.months + ' months</div><p style="margin-top:10px"><strong>Items:</strong></p>' + s.items.map(i => '<div class="list-item">• ' + esc(i) + '</div>').join('') + '</div>').join('');
}

// ═══ BOOK TIME ═══
let bookData = [];
async function loadBookTime(){ if (!bookData.length){ try { bookData = (await jget('/api/book-times')).times; } catch(e){ return; } } filterBook(); }
async function loadBookTimes(){
  if (!bookData.length){ try { bookData = (await jget('/api/book-times')).times; } catch(e){ return; } }
  const opts = '<option value="">— Auto labour —</option>' + bookData.map(b => '<option value="' + b.hrs + '">' + esc(b.job) + ' (' + b.hrs + 'h)</option>').join('');
  const sq = document.getElementById('qBookTime'); if (sq) sq.innerHTML = opts;
  const si = document.getElementById('iBookTime'); if (si) si.innerHTML = opts;
}
function filterBook(){
  const q = (document.getElementById('bookSearch').value || '').toLowerCase();
  const f = bookData.filter(x => !q || x.job.toLowerCase().includes(q));
  document.getElementById('bookList').innerHTML = f.map(b => '<div class="card"><h3>⏱️ ' + esc(b.job) + '</h3><div class="list-item"><strong>Standard time:</strong> ' + b.hrs + ' hours</div></div>').join('');
}
async function applyBookTime(prefix){
  const h = parseFloat(document.getElementById(prefix + 'BookTime').value) || 0;
  if (!h) return;
  const rate = await getRate();
  document.getElementById(prefix + 'Labour').value = (h * rate).toFixed(2);
  toast('Labour: R' + (h * rate).toFixed(2), 'info');
}
async function getRate(){ try { const r = await jget('/api/workshop'); return r.labour_rate || 450; } catch(e){ return 450; } }

// ═══ SUPPLIERS ═══
async function loadSuppliers(){
  const c = document.getElementById('supplierList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/suppliers');
    c.innerHTML = d.suppliers.length ? d.suppliers.map(s => '<div class="card"><h3>📞 ' + esc(s.name) + '</h3>' + (s.category ? '<p style="font-size:12px;color:var(--text2)">' + esc(s.category) + '</p>' : '') + (s.phone ? '<p>📞 ' + esc(s.phone) + '</p>' : '') + (s.email ? '<p>📧 ' + esc(s.email) + '</p>' : '') + (s.account_number ? '<p>Account: ' + esc(s.account_number) + '</p>' : '') + '<div style="margin-top:10px">' + (s.phone ? '<button class="btn-sm blue" onclick="window.location.href=\'tel:' + esc(s.phone) + '\'">📞 Call</button>' : '') + (s.whatsapp ? '<button class="btn-sm wa" onclick="window.open(\'https://wa.me/' + esc(s.whatsapp).replace(/[^0-9]/g,'') + '\',\'_blank\')">📱 WhatsApp</button>' : '') + '<button class="btn-sm red" onclick="delSupplier(\'' + s.id + '\')">Delete</button></div></div>').join('') : emptyState('📞','No suppliers yet','');
  } catch(e){ c.innerHTML = emptyState('❌','Error',''); }
}
async function addSupplier(){
  const n = document.getElementById('supName').value.trim();
  if (!n){ toast('Name required', 'warning'); return; }
  await jpost('/api/suppliers', { name:n, phone:document.getElementById('supPhone').value, email:document.getElementById('supEmail').value, whatsapp:document.getElementById('supWhatsapp').value, category:document.getElementById('supCategory').value, account_number:document.getElementById('supAccount').value, notes:document.getElementById('supNotes').value });
  ['supName','supPhone','supEmail','supWhatsapp','supCategory','supAccount','supNotes'].forEach(id => document.getElementById(id).value = '');
  hideForm('supplierForm'); toast('Supplier added', 'success'); loadSuppliers();
}
async function delSupplier(id){ if (!confirm('Delete?')) return; await fetch('/api/suppliers/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadSuppliers(); }

// ═══ CODES ═══
async function searchCodes(){
  const q = document.getElementById('codeSearch').value;
  const c = document.getElementById('codeResults');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/fault-codes?search=' + encodeURIComponent(q));
    c.dataset.loaded = '1';
    c.innerHTML = d.codes.length ? d.codes.map(x => '<div class="card"><h3>' + x.code + '<span class="badge ' + x.severity.toLowerCase() + '">' + x.severity + '</span></h3><p><strong>' + esc(x.description) + '</strong></p><p style="color:var(--text2);font-size:12px">' + esc(x.system) + '</p><p style="margin-top:8px"><strong>Causes:</strong></p>' + x.causes.map(y => '<div class="list-item">• ' + esc(y) + '</div>').join('') + '<p style="margin-top:8px"><strong>Steps:</strong></p>' + x.steps.map(y => '<div class="list-item">• ' + esc(y) + '</div>').join('') + '</div>').join('') : emptyState('📟','No codes match','');
  } catch(e){ c.innerHTML = ''; toast('Failed', 'error'); }
}

// ═══ JOBS ═══
let jobBeforePhotos = [];
async function addPhoto(e){ for (const f of Array.from(e.target.files)){ jobBeforePhotos.push(await compressImage(f, 1000, 0.7)); } renderJobPhotos(); }
function renderJobPhotos(){ document.getElementById('beforeRow').innerHTML = jobBeforePhotos.map((p, i) => '<div style="position:relative"><img class="photo-thumb" src="' + p + '"><button class="btn-sm red" style="position:absolute;top:-5px;right:-5px;width:24px;height:24px;padding:0;border-radius:50%" onclick="jobBeforePhotos.splice(' + i + ',1);renderJobPhotos()">×</button></div>').join(''); }
async function loadStaffDropdown(){ try { const d = await jget('/api/staff'); const sel = document.getElementById('jAssigned'); if (sel) sel.innerHTML = '<option value="">— Assign —</option>' + d.staff.map(s => '<option value="' + esc(s.name) + '">' + esc(s.name) + '</option>').join(''); } catch(e){} }
async function loadJobs(){
  const c = document.getElementById('jobList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/jobs');
    c.innerHTML = d.jobs.length ? d.jobs.map(j => { const ph = j.photos_before && j.photos_before.length ? '<div class="photo-row">' + j.photos_before.map(p => '<img class="photo-thumb" src="' + p + '">').join('') + '</div>' : ''; return '<div class="card"><h3>Job #' + j.id + ' <span class="badge ' + j.status.toLowerCase().replace(' ','') + '">' + j.status + '</span></h3><p><strong>' + esc(j.customer) + '</strong></p><p>🚗 ' + esc(j.vehicle) + '</p>' + (j.assigned_to ? '<p style="color:var(--text2);font-size:12px">👷 ' + esc(j.assigned_to) + '</p>' : '') + '<p style="color:var(--text2)">' + esc(j.complaint) + '</p>' + ph + '<div style="margin-top:10px"><button class="btn-sm blue" onclick="upJob(\'' + j.id + '\',\'In Progress\')">Progress</button><button class="btn-sm green" onclick="upJob(\'' + j.id + '\',\'Completed\')">Done</button><button class="btn-sm wa" onclick="waJob(\'' + j.id + '\')">📱</button><button class="btn-sm red" onclick="delJob(\'' + j.id + '\')">Delete</button></div></div>'; }).join('') : emptyState('📋','No jobs yet','Tap + New Job to create.');
  } catch(e){ c.innerHTML = emptyState('❌','Error',''); }
}
async function createJob(){
  const c = document.getElementById('jCustomer').value.trim();
  const v = document.getElementById('jVehicle').value.trim();
  const comp = document.getElementById('jComplaint').value.trim();
  if (!c || !v || !comp){ toast('Fill required fields', 'warning'); return; }
  await jpost('/api/jobs', { customer:c, phone:document.getElementById('jPhone').value, vehicle:v, registration:document.getElementById('jReg').value, complaint:comp, assigned_to:document.getElementById('jAssigned').value, warranty_months:parseInt(document.getElementById('jWarranty').value) || 6, photos_before:jobBeforePhotos });
  ['jCustomer','jPhone','jVehicle','jReg','jComplaint'].forEach(id => document.getElementById(id).value = '');
  jobBeforePhotos = []; renderJobPhotos(); hideForm('jobForm'); toast('Job created ✓', 'success'); loadJobs();
}
async function upJob(id, s){ await jput('/api/jobs/' + id, {status:s}); toast('Updated', 'success'); loadJobs(); }
async function delJob(id){ if (!confirm('Delete?')) return; await fetch('/api/jobs/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadJobs(); }
function waJob(id){ jget('/api/jobs').then(d => { const j = d.jobs.find(x => x.id == id); const txt = '🔧 Job #' + j.id + '\n' + j.customer + '\nStatus: ' + j.status; window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank'); }); }

// ═══ QUOTES ═══
async function loadQuotes(){
  const c = document.getElementById('quoteList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/quotes');
    c.innerHTML = d.quotes.length ? d.quotes.map(q => '<div class="card"><h3>💬 Quote #' + q.id + '</h3><p><strong>' + esc(q.customer) + '</strong></p><p>' + esc(q.description) + '</p><div class="list-item"><strong>Total: R' + q.total.toFixed(2) + '</strong></div><div style="margin-top:10px"><button class="btn-sm green" onclick="acceptQuote(\'' + q.id + '\')">→ Invoice</button><button class="btn-sm red" onclick="delQuote(\'' + q.id + '\')">Delete</button></div></div>').join('') : emptyState('💬','No quotes yet','');
  } catch(e){ c.innerHTML = emptyState('❌','Error',''); }
}
async function createQuote(){
  const c = document.getElementById('qCustomer').value.trim();
  const d = document.getElementById('qDesc').value.trim();
  if (!c || !d){ toast('Fill required', 'warning'); return; }
  await jpost('/api/quotes', { customer:c, vehicle:document.getElementById('qVehicle').value, description:d, labour:parseFloat(document.getElementById('qLabour').value) || 0, parts:parseFloat(document.getElementById('qParts').value) || 0 });
  ['qCustomer','qVehicle','qDesc','qLabour','qParts'].forEach(id => document.getElementById(id).value = '');
  hideForm('quoteForm'); toast('Quote created ✓', 'success'); loadQuotes();
}
async function acceptQuote(id){ if (!confirm('Convert?')) return; const r = await jpost('/api/quotes/' + id + '/accept', {}); if (r.success){ toast('Converted ✓', 'success'); loadQuotes(); } }
async function delQuote(id){ if (!confirm('Delete?')) return; await fetch('/api/quotes/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadQuotes(); }

// ═══ APPTS ═══
async function loadAppts(){
  const c = document.getElementById('apptList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/appointments');
    const s = d.appointments.sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time));
    c.innerHTML = s.length ? s.map(a => '<div class="card"><h3>📅 ' + esc(a.date) + ' at ' + esc(a.time) + '</h3><p><strong>' + esc(a.customer) + '</strong></p>' + (a.vehicle ? '<p>🚗 ' + esc(a.vehicle) + '</p>' : '') + '<button class="btn-sm red" onclick="delAppt(\'' + a.id + '\')">Delete</button></div>').join('') : emptyState('📅','No appointments','');
  } catch(e){ c.innerHTML = emptyState('❌','Error',''); }
}
async function createAppt(){
  const c = document.getElementById('aCustomer').value.trim();
  const d = document.getElementById('aDate').value;
  const t = document.getElementById('aTime').value;
  if (!c || !d || !t){ toast('Fill required', 'warning'); return; }
  await jpost('/api/appointments', { customer:c, phone:document.getElementById('aPhone').value, vehicle:document.getElementById('aVehicle').value, service:document.getElementById('aService').value, date:d, time:t });
  ['aCustomer','aPhone','aVehicle','aService','aDate','aTime'].forEach(id => document.getElementById(id).value = '');
  hideForm('apptForm'); toast('Booked ✓', 'success'); loadAppts();
}
async function delAppt(id){ if (!confirm('Delete?')) return; await fetch('/api/appointments/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadAppts(); }

// ═══ CUSTOMERS ═══
async function loadCust(){
  const c = document.getElementById('custList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/customers');
    c.innerHTML = d.customers.length ? d.customers.map(x => '<div class="card"><h3>👤 ' + esc(x.name) + '</h3><p>📞 ' + esc(x.phone) + '</p>' + (x.email ? '<p>📧 ' + esc(x.email) + '</p>' : '') + '<div style="margin-top:10px"><button class="btn-sm wa" onclick="waCust(\'' + esc(x.phone) + '\')">📱</button><button class="btn-sm red" onclick="delCust(\'' + x.id + '\')">Delete</button></div></div>').join('') : emptyState('👥','No customers yet','');
  } catch(e){ c.innerHTML = emptyState('❌','Error',''); }
}
async function createCustomer(){
  const n = document.getElementById('cName').value.trim();
  const p = document.getElementById('cPhone').value.trim();
  if (!n || !p){ toast('Name + phone required', 'warning'); return; }
  await jpost('/api/customers', {name:n, phone:p, email:document.getElementById('cEmail').value});
  ['cName','cPhone','cEmail'].forEach(id => document.getElementById(id).value = '');
  hideForm('custForm'); toast('Customer added ✓', 'success'); loadCust();
}
async function delCust(id){ if (!confirm('Delete?')) return; await fetch('/api/customers/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadCust(); }
function waCust(p){ window.open('https://wa.me/' + p.replace(/[^0-9]/g,''), '_blank'); }

// ═══ INVOICES ═══
async function loadInv(){
  const c = document.getElementById('invList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/invoices');
    c.innerHTML = d.invoices.length ? d.invoices.map(i => '<div class="card" id="inv-' + i.id + '"><h3>Inv #' + i.id + '</h3><p><strong>' + esc(i.customer) + '</strong></p><p>' + esc(i.description) + '</p><div class="list-item">Labour: R' + i.labour.toFixed(2) + '</div><div class="list-item">Parts: R' + i.parts.toFixed(2) + '</div><div class="list-item"><strong>Total: R' + i.total.toFixed(2) + '</strong></div><div style="margin-top:10px"><button class="btn-sm wa" onclick="waInv(\'' + i.id + '\')">📱</button><button class="btn-sm blue" onclick="printInv(\'' + i.id + '\')">🖨</button><button class="btn-sm red" onclick="delInv(\'' + i.id + '\')">Delete</button></div></div>').join('') : emptyState('💰','No invoices yet','');
  } catch(e){ c.innerHTML = emptyState('❌','Error',''); }
}
async function createInvoice(){
  const c = document.getElementById('iCustomer').value.trim();
  const d = document.getElementById('iDesc').value.trim();
  if (!c || !d){ toast('Fill required', 'warning'); return; }
  await jpost('/api/invoices', { customer:c, vehicle:document.getElementById('iVehicle').value, description:d, labour:parseFloat(document.getElementById('iLabour').value) || 0, parts:parseFloat(document.getElementById('iParts').value) || 0 });
  ['iCustomer','iVehicle','iDesc','iLabour','iParts'].forEach(id => document.getElementById(id).value = '');
  hideForm('invForm'); toast('Invoice created ✓', 'success'); loadInv();
}
async function delInv(id){ if (!confirm('Delete?')) return; await fetch('/api/invoices/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadInv(); }
function waInv(id){ jget('/api/invoices').then(d => { const i = d.invoices.find(x => x.id == id); const txt = '💰 Invoice #' + i.id + '\n' + i.customer + '\nTotal: R' + i.total.toFixed(2); window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank'); }); }
function printInv(id){
  jget('/api/invoices').then(async d => {
    const i = d.invoices.find(x => x.id == id);
    const ws = await jget('/api/workshop');
    const w = window.open('', '', 'width=800,height=600');
    w.document.write('<html><head><title>Invoice #' + i.id + '</title><style>body{font-family:Arial;padding:20px;max-width:600px;margin:auto}h1{color:#E65100;border-bottom:2px solid #E65100;padding-bottom:8px}h2{color:#333}.row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #eee}.total{font-size:20px;font-weight:bold;color:#E65100;border-top:2px solid #E65100;padding-top:8px}.terms{margin-top:24px;font-size:11px;color:#666;border-top:1px dashed #ccc;padding-top:12px}</style></head><body>');
    w.document.write('<h1>' + (ws.logo || '🔧') + ' ' + esc(ws.name || 'Workshop') + '</h1>');
    w.document.write('<p>' + esc(ws.phone || '') + ' | ' + esc(ws.email || '') + '<br>' + esc(ws.address || '') + '</p>');
    w.document.write('<h2>Invoice #' + i.id + '</h2>');
    w.document.write('<p><strong>Customer:</strong> ' + esc(i.customer) + '<br><strong>Vehicle:</strong> ' + esc(i.vehicle || '-') + '</p>');
    w.document.write('<div class="row"><span>' + esc(i.description) + '</span><span></span></div>');
    w.document.write('<div class="row"><span>Labour</span><span>R' + i.labour.toFixed(2) + '</span></div>');
    w.document.write('<div class="row"><span>Parts</span><span>R' + i.parts.toFixed(2) + '</span></div>');
    w.document.write('<div class="row"><span>VAT</span><span>R' + i.vat.toFixed(2) + '</span></div>');
    w.document.write('<div class="row total"><span>TOTAL</span><span>R' + i.total.toFixed(2) + '</span></div>');
    if (ws.bank_details) w.document.write('<p><strong>Bank:</strong> ' + esc(ws.bank_details) + '</p>');
    w.document.write('<div class="terms"><strong>Terms:</strong><br>' + esc(ws.terms || 'Payment due within 30 days.') + '</div>');
    w.document.write('</body></html>');
    w.document.close(); setTimeout(() => w.print(), 500);
  });
}

// ═══ INVENTORY ═══
async function loadInventory(){
  const c = document.getElementById('inventoryList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/inventory');
    c.innerHTML = d.items.length ? d.items.map(i => { const cls = i.qty <= i.min_qty ? 'warn' : 'ok'; return '<div class="card"><h3>' + esc(i.name) + ' <span class="badge ' + cls + '">' + i.qty + '</span></h3><div class="list-item">Cost R' + i.cost_price.toFixed(2) + ' | Sell R' + i.sell_price.toFixed(2) + '</div><div style="margin-top:10px"><button class="btn-sm green" onclick="adjInv(\'' + i.id + '\',1)">+1</button><button class="btn-sm red" onclick="adjInv(\'' + i.id + '\',-1)">-1</button><button class="btn-sm gray" onclick="delInvItem(\'' + i.id + '\')">Delete</button></div></div>'; }).join('') : emptyState('📦','No stock','');
  } catch(e){ c.innerHTML = emptyState('❌','Error',''); }
}
async function addInventory(){
  const n = document.getElementById('pName').value.trim();
  if (!n){ toast('Name required', 'warning'); return; }
  await jpost('/api/inventory', { part_number:document.getElementById('pNumber').value, name:n, category:document.getElementById('pCategory').value, qty:parseInt(document.getElementById('pQty').value) || 0, min_qty:parseInt(document.getElementById('pMinQty').value) || 5, cost_price:parseFloat(document.getElementById('pCost').value) || 0, sell_price:parseFloat(document.getElementById('pSell').value) || 0, supplier:document.getElementById('pSupplier').value });
  ['pNumber','pName','pCategory','pQty','pMinQty','pCost
  from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import openai, os, uuid, csv, io, json

# ═══════════════════════════════════
# CONFIG
# ═══════════════════════════════════
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# ═══════════════════════════════════
# DATABASE (Supabase + memory fallback)
# ═══════════════════════════════════
_db = None
DB_READY = False

def init_db():
    global _db, DB_READY
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[db] Memory mode"); return
    try:
        from supabase import create_client
        _db = create_client(SUPABASE_URL, SUPABASE_KEY)
        _db.table("workshop").select("id").limit(1).execute()
        DB_READY = True
        print("[db] Supabase connected")
    except Exception as e:
        print(f"[db] Failed: {e}")
        DB_READY = False

init_db()

MEM = {"jobs":{}, "customers":{}, "invoices":{}, "quotes":{}, "appointments":{},
       "inventory":{}, "staff":{}, "expenses":{}, "suppliers":{}}

WORKSHOP = {"name":"My Workshop","phone":"","email":"","address":"","hours":"",
            "logo":"🔧","labour_rate":450,"vat_number":"","company_reg":"",
            "bank_details":"","terms":"Payment due within 30 days."}

def db_list(t):
    if DB_READY:
        try: return _db.table(t).select("*").execute().data or []
        except Exception as e: print(f"[db] {t}: {e}")
    return list(MEM[t].values())

def db_get(t, i):
    if DB_READY:
        try:
            r = _db.table(t).select("*").eq("id", i).execute()
            return r.data[0] if r.data else None
        except Exception as e: print(f"[db] get {t}: {e}")
    return MEM[t].get(i)

def db_save(t, i, row):
    if DB_READY:
        try:
            if db_get(t,i): _db.table(t).update(row).eq("id",i).execute()
            else: _db.table(t).insert(row).execute()
            return row
        except Exception as e: print(f"[db] save {t}: {e}")
    MEM[t][i] = row
    return row

def db_del(t, i):
    if DB_READY:
        try: _db.table(t).delete().eq("id",i).execute(); return True
        except Exception as e: print(f"[db] del {t}: {e}"); return False
    MEM[t].pop(i,None); return True

def ws_get():
    if DB_READY:
        try:
            r = _db.table("workshop").select("*").eq("id",1).execute()
            if r.data: return r.data[0]
        except Exception as e: print(f"[db] ws: {e}")
    return WORKSHOP

def ws_save(d):
    if DB_READY:
        try: _db.table("workshop").update(d).eq("id",1).execute(); return d
        except Exception as e: print(f"[db] ws save: {e}")
    WORKSHOP.update(d); return WORKSHOP

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M")
def today(): return datetime.now().strftime("%Y-%m-%d")

# ═══════════════════════════════════
# REFERENCE DATA
# ═══════════════════════════════════
FAULT_CODES = {
    "P0101":{"code":"P0101","description":"Mass Air Flow Circuit","system":"Engine","severity":"Medium","causes":["Dirty MAF","Air leaks","Clogged filter"],"steps":["Check filter","Inspect intake","Clean MAF"]},
    "P0300":{"code":"P0300","description":"Multiple Cylinder Misfire","system":"Engine","severity":"High","causes":["Faulty plugs","Bad coils","Fuel issues"],"steps":["Scan cylinders","Check plugs","Test coils"]},
    "P0401":{"code":"P0401","description":"EGR Flow Insufficient","system":"Engine","severity":"Medium","causes":["Clogged EGR","Blocked passages"],"steps":["Inspect EGR","Check passages"]},
    "P0700":{"code":"P0700","description":"Transmission Control","system":"Transmission","severity":"High","causes":["Internal fault","TCM problem","Solenoid"],"steps":["Scan TCM","Check fluid"]},
    "P0087":{"code":"P0087","description":"Fuel Rail Pressure Low","system":"Diesel","severity":"High","causes":["Faulty HP pump","Clogged filter"],"steps":["Check pressure","Inspect filter"]},
    "HYD-001":{"code":"HYD-001","description":"Low Hydraulic Pressure","system":"Hydraulic","severity":"High","causes":["Worn pump","Leaks","Low fluid"],"steps":["Check fluid","Test pressure"]},
    "PNEU-001":{"code":"PNEU-001","description":"Air Compressor No Pressure","system":"Pneumatic","severity":"High","causes":["Worn rings","Leaking valves"],"steps":["Check belt","Test output"]},
}

WMI_DB = {"1HG":("Honda","USA"),"1FT":("Ford","USA"),"JHM":("Honda","Japan"),"JTD":("Toyota","Japan"),
          "JTM":("Toyota","Japan"),"KMH":("Hyundai","Korea"),"KNA":("Kia","Korea"),"WBA":("BMW","Germany"),
          "WDB":("Mercedes-Benz","Germany"),"WVW":("Volkswagen","Germany"),"YV1":("Volvo","Sweden"),
          "ZFA":("Fiat","Italy"),"AAV":("VW SA","South Africa"),"AHT":("Toyota SA","South Africa"),
          "AFA":("Ford SA","South Africa"),"ADB":("Mercedes SA","South Africa")}
YEAR_CODES = {"A":2010,"B":2011,"C":2012,"D":2013,"E":2014,"F":2015,"G":2016,"H":2017,"J":2018,"K":2019,"L":2020,"M":2021,"N":2022,"P":2023,"R":2024,"Y":2000,"1":2001,"2":2002,"3":2003,"4":2004,"5":2005,"6":2006,"7":2007,"8":2008,"9":2009}

TORQUE = [
    {"s":"M6","g":"8.8","nm":10,"ft":7.4,"u":"Small brackets"},{"s":"M8","g":"8.8","nm":25,"ft":18.4,"u":"Engine brackets"},
    {"s":"M10","g":"8.8","nm":50,"ft":37,"u":"Subframe bolts"},{"s":"M12","g":"8.8","nm":90,"ft":66,"u":"Wheel hubs"},
    {"s":"M14","g":"8.8","nm":140,"ft":103,"u":"Heavy brackets"},{"s":"M16","g":"8.8","nm":215,"ft":159,"u":"Chassis bolts"},
    {"s":"M8","g":"10.9","nm":35,"ft":25.8,"u":"Head (small)"},{"s":"M10","g":"10.9","nm":70,"ft":51.6,"u":"Head bolts"},
    {"s":"M12","g":"10.9","nm":120,"ft":88.5,"u":"Head bolts"},{"s":"M14","g":"10.9","nm":190,"ft":140,"u":"Diesel head"},
    {"s":"M12","g":"12.9","nm":145,"ft":107,"u":"Racing"},{"s":"M10","g":"12.9","nm":83,"ft":61.2,"u":"Performance"},
]
SEQ = [
    {"c":"Cylinder Head — 4 Cyl","st":["Stage 1: 40 Nm","Stage 2: 80 Nm","Stage 3: +90°","Stage 4: +90°"]},
    {"c":"Wheel Nuts — Car","st":["Stage 1: 60 Nm","Final: 110 Nm"]},
    {"c":"Wheel Nuts — Bakkie","st":["Stage 1: 100 Nm","Final: 140 Nm"]},
    {"c":"Spark Plugs","st":["Cast iron: 25 Nm","Aluminum: 18 Nm"]},
    {"c":"Oil Drain Plug","st":["Steel M12: 25 Nm","Alum M12: 18 Nm"]},
]
BULBS = [
    {"v":"Toyota Hilux (2015+)","l":"H11","h":"HB3","f":"H16","r":"W16W"},
    {"v":"Ford Ranger","l":"H11","h":"HB3","f":"H11","r":"P21W"},
    {"v":"VW Polo","l":"H7","h":"H7","f":"H8","r":"P21W"},
    {"v":"BMW 3-Series","l":"H7 / Xenon","h":"H7","f":"H8","r":"P21W"},
    {"v":"Isuzu D-Max","l":"H11","h":"HB3","f":"H11","r":"P21W"},
]
BATTERIES = [
    {"v":"Toyota Hilux 2.8 GD-6","g":"DIN 66L","c":680,"a":70},
    {"v":"Ford Ranger 2.2 TDCi","g":"DIN 66L","c":660,"a":68},
    {"v":"VW Polo / Golf","g":"DIN 44L","c":330,"a":44},
    {"v":"BMW 3-Series","g":"DIN 80L","c":800,"a":80},
]
TYRES = [
    {"v":"Toyota Hilux","s":"265/65R17","f":"2.2 bar","r":"2.4 bar"},
    {"v":"Ford Ranger","s":"265/65R17","f":"2.2 bar","r":"2.4 bar"},
    {"v":"VW Polo","s":"185/60R15","f":"2.1 bar","r":"2.1 bar"},
]
WIRING = [
    {"n":"Charging System","sy":"Charging","d":"Alternator, battery, warning light",
     "c":["Battery 12V","Alternator","Ignition switch","Warning light"],
     "co":["Battery + → Alt B+ (Red, 6mm²)","Battery - → Ground","Alt D+ → Warning light","Warning light → IGN 15"]},
    {"n":"Starting System","sy":"Starting","d":"Starter, relay, ignition",
     "c":["Battery","Ignition switch","Starter relay","Starter motor"],
     "co":["Battery + → Starter 30 (25mm²)","IGN 50 → Relay 86","Relay 87 → Starter 50"]},
    {"n":"Engine Sensors","sy":"Engine","d":"MAF, MAP, TPS, ECT, O2 to ECU",
     "c":["ECU","MAF","MAP","TPS","ECT","O2"],
     "co":["ECU → MAF: signal+ground+power","ECU → MAP: signal+ground+5V","ECU → TPS: 5V+signal+ground"]},
]
PIDS = [
    {"p":"0100","n":"PIDs supported","d":"Bit-encoded supported"},
    {"p":"0101","n":"Monitor status","d":"MIL + readiness"},
    {"p":"0105","n":"Engine coolant temp","d":"°C"},
    {"p":"010C","n":"Engine RPM","d":"((A*256)+B)/4"},
    {"p":"010D","n":"Vehicle speed","d":"km/h"},
    {"p":"010F","n":"Intake air temp","d":"°C"},
    {"p":"0110","n":"MAF flow rate","d":"g/s"},
    {"p":"0111","n":"Throttle position","d":"%"},
    {"p":"0142","n":"Control module voltage","d":"V"},
]
VEHICLE_SPECS = [
    {"v":"Toyota Hilux 2.8 GD-6","oil":"7.5L 5W-30","coolant":"8.2L SLLC","brake":"DOT 4","trans":"ATF WS 3.5L","engine_code":"1GD-FTV","timing":"Chain"},
    {"v":"Ford Ranger 2.2 TDCi","oil":"6.8L 5W-30","coolant":"9.0L Motorcraft","brake":"DOT 4","trans":"ATF Mercon LV","engine_code":"P4AT","timing":"Belt @150k"},
    {"v":"VW Polo 1.4","oil":"3.8L 5W-30","coolant":"5.5L G13","brake":"DOT 4","trans":"75W-90","engine_code":"CLPA","timing":"Chain"},
    {"v":"BMW 320i (F30)","oil":"5.0L 0W-40","coolant":"7.0L BMW Blue","brake":"DOT 4","trans":"ATF ZF 8HP","engine_code":"N20B20","timing":"Chain"},
    {"v":"Isuzu D-Max 2.5","oil":"6.5L 15W-40","coolant":"7.8L Isuzu Blue","brake":"DOT 4","trans":"ATF Dexron III","engine_code":"4JK1-TC","timing":"Chain"},
]
INTERVALS = [
    {"t":"Petrol Vehicle","km":15000,"months":12,"items":["Oil + filter","Air filter","Spark plugs check","Brake inspection"]},
    {"t":"Diesel Vehicle","km":10000,"months":6,"items":["Oil + filter","Fuel filter","Air filter","Water separator drain"]},
    {"t":"Truck / Heavy Diesel","km":25000,"months":6,"items":["Oil + filters","Fuel filter","Air dryer","Brake check"]},
]
BOOK_TIMES = [
    {"job":"Oil + Filter (Petrol)","hrs":0.5},{"job":"Oil + Filter (Diesel)","hrs":1.0},
    {"job":"Brake Pads Front","hrs":1.5},{"job":"Clutch Replacement","hrs":6.0},
    {"job":"Timing Belt","hrs":4.0},{"job":"Head Gasket","hrs":12.0},
    {"job":"Water Pump","hrs":4.0},{"job":"Alternator","hrs":2.0},
    {"job":"Diagnostic Scan","hrs":0.5},
]

# ═══════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════
app = FastAPI(title="RamsTech", version="18.0")

# CORS - allow all origins (mobile apps + web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# ═══ HEALTH - FAST, NO DB HIT ═══
@app.get("/health")
def health():
    return {"status":"ok","time":datetime.now().isoformat()}

@app.get("/ping")
def ping():
    return "pong"

# ═══ REFERENCE ═══
@app.get("/api/fault-codes")
def codes(search: str = None):
    r = list(FAULT_CODES.values())
    if search:
        q = search.lower()
        r = [c for c in r if q in c["code"].lower() or q in c["description"].lower()]
    return {"codes": r}

@app.get("/api/specs")
def specs(): return {"specs": VEHICLE_SPECS}

@app.get("/api/intervals")
def intervals(): return {"intervals": INTERVALS}

@app.get("/api/book-times")
def book_times(): return {"times": BOOK_TIMES}

@app.get("/api/torque")
def torque(): return {"bolts": TORQUE, "sequences": SEQ}

@app.get("/api/bulbs")
def bulbs(): return {"bulbs": BULBS}

@app.get("/api/batteries")
def batteries(): return {"batteries": BATTERIES}

@app.get("/api/tyres")
def tyres(): return {"tyres": TYRES}

@app.get("/api/wiring")
def wiring(): return {"circuits": WIRING}

@app.get("/api/obd-pids")
def obd_pids(): return {"pids": PIDS}

@app.get("/api/vin/{vin}")
def decode_vin(vin: str):
    v = vin.strip().upper()
    if len(v) != 17: raise HTTPException(400,"VIN must be exactly 17 characters")
    mfr, country = WMI_DB.get(v[:3], ("Unknown","Unknown"))
    return {"vin":v,"manufacturer":mfr,"country":country,"year":YEAR_CODES.get(v[9],"Unknown"),"plant":"Unknown","serial":v[11:]}

@app.post("/api/bolt-calc")
async def bolt_calc(r: Request):
    d = await r.json(); size = d.get("size","M8"); grade = d.get("grade","8.8"); cond = d.get("condition","dry")
    tm = {"8.8":800,"10.9":1040,"12.9":1220}
    am = {"M6":20.1,"M8":36.6,"M10":58.0,"M12":84.3,"M14":115.0,"M16":157.0,"M20":245.0}
    km = {"dry":0.20,"oiled":0.17,"moly":0.14}
    ts = tm.get(grade,800); a = am.get(size,36.6); k = km.get(cond,0.20)
    cf = 0.75*ts*a; dm = float(size.replace("M",""))/1000.0; nm = k*dm*cf
    return {"size":size,"grade":grade,"condition":cond,"nm":nm,"ftlb":nm*0.73756,"clamp_kn":cf/1000}

# ═══ AI ═══
@app.post("/api/chat")
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

@app.post("/api/diagnose/photo")
async def diagnose_photo(r: Request):
    d = await r.json(); img = d.get("image_base64",""); veh = d.get("vehicle_info","")
    if not img: raise HTTPException(400,"Image required")
    if not OPENAI_KEY: return {"success":False,"error":"AI not configured"}
    if img.startswith("data:"): img = img.split(",",1)[1]
    if len(img) > 7_000_000: return {"success":False,"error":"Image too large"}
    p = f"""Expert mechanic. Vehicle: {veh or 'N/A'}
Respond ONLY JSON: {{"problem":"S","description":"D","confidence":"High|Medium|Low","possible_causes":["C"],"diagnostic_steps":["S"],"safety_warnings":["W"]}}"""
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        resp = c.chat.completions.create(model="gpt-4o", messages=[{"role":"user","content":[{"type":"text","text":p},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}], max_tokens=2000, temperature=0.2, response_format={"type":"json_object"})
        parsed = json.loads(resp.choices[0].message.content); parsed["success"]=True; return parsed
    except Exception as e: return {"success":False,"error":str(e)}

@app.post("/api/paint/match")
async def match_paint(r: Request):
    d = await r.json(); img = d.get("image_base64",""); veh = d.get("vehicle_info","")
    if not img: raise HTTPException(400,"Image required")
    if not OPENAI_KEY: return {"success":False,"error":"AI not configured"}
    if img.startswith("data:"): img = img.split(",",1)[1]
    if len(img) > 7_000_000: return {"success":False,"error":"Image too large"}
    p = f"""Expert paint tech. Vehicle: {veh or 'N/A'}
Respond ONLY JSON: {{"detected_colour":{{"name":"N","hex_code":"#RRGGBB","finish":"Solid|Metallic|Pearl","colour_family":"White|Black|Red|Blue|Silver|Grey"}},"confidence":"High|Medium|Low","brand_codes":[{{"brand":"DuPont","code":"C"}}],"safety_warnings":["W"]}}"""
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        resp = c.chat.completions.create(model="gpt-4o", messages=[{"role":"user","content":[{"type":"text","text":p},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}], max_tokens=2000, temperature=0.2, response_format={"type":"json_object"})
        parsed = json.loads(resp.choices[0].message.content); parsed["success"]=True; return parsed
    except Exception as e: return {"success":False,"error":str(e)}

# ═══ STATS ═══
@app.get("/api/stats")
def stats():
    jobs = db_list("jobs"); invs = db_list("invoices"); custs = db_list("customers"); exps = db_list("expenses")
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

@app.get("/api/analytics")
def analytics():
    jobs = db_list("jobs"); invs = db_list("invoices")
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

@app.get("/api/warranty")
def warranty_list():
    items = []
    for j in db_list("jobs"):
        if j.get("status")=="Completed" and int(j.get("warranty_months",0) or 0)>0:
            try:
                done = datetime.strptime((j.get("created") or "")[:10],"%Y-%m-%d"); months = int(j["warranty_months"])
                year = done.year + (done.month+months-1)//12; month = ((done.month+months-1)%12)+1
                expiry = done.replace(year=year,month=month); days_left = (expiry-datetime.now()).days
                items.append({"id":j["id"],"customer":j.get("customer",""),"vehicle":j.get("vehicle",""),"expiry":expiry.strftime("%Y-%m-%d"),"days_left":days_left,"status":"active" if days_left>0 else "expired"})
            except Exception: pass
    items.sort(key=lambda x:x["days_left"]); return {"warranties":items}

@app.get("/api/export/tax")
def export_tax(from_date: str = None, to_date: str = None):
    o = io.StringIO(); w = csv.writer(o)
    w.writerow(["Date","Type","Description","Customer/Note","Amount","VAT"])
    for i in db_list("invoices"):
        d = (i.get("created") or "")[:10]
        if from_date and d < from_date: continue
        if to_date and d > to_date: continue
        w.writerow([d,"INCOME",i.get("description",""),i.get("customer",""),f"{float(i.get('total',0)):.2f}",f"{float(i.get('vat',0)):.2f}"])
    for e in db_list("expenses"):
        d = e.get("date","")
        if from_date and d < from_date: continue
        if to_date and d > to_date: continue
        w.writerow([d,"EXPENSE",e.get("category",""),e.get("note",""),f"-{float(e.get('amount',0)):.2f}","0.00"])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=tax_report.csv"})

# ═══ JOBS ═══
@app.get("/api/jobs")
def list_jobs(): return {"jobs": db_list("jobs")}

@app.post("/api/jobs")
async def create_job(r: Request):
    d = await r.json(); jid = str(uuid.uuid4())[:6]
    row = {"id":jid,"customer":d.get("customer",""),"phone":d.get("phone",""),"vehicle":d.get("vehicle",""),"registration":d.get("registration",""),"complaint":d.get("complaint",""),"assigned_to":d.get("assigned_to",""),"warranty_months":int(d.get("warranty_months",6)),"photos_before":d.get("photos_before",[]),"photos_after":[],"signature":"","status":"New","created":now()}
    db_save("jobs", jid, row); return {"success":True,"job":row}

@app.put("/api/jobs/{jid}")
async def update_job(jid: str, r: Request):
    d = await r.json(); job = db_get("jobs", jid)
    if job:
        job["status"] = d.get("status", job["status"])
        db_save("jobs", jid, job)
    return {"success":True}

@app.delete("/api/jobs/{jid}")
def delete_job(jid: str): db_del("jobs",jid); return {"success":True}

# ═══ CUSTOMERS ═══
@app.get("/api/customers")
def list_cust(): return {"customers": db_list("customers")}

@app.post("/api/customers")
async def create_cust(r: Request):
    d = await r.json(); cid = str(uuid.uuid4())[:6]
    row = {"id":cid,"name":d.get("name",""),"phone":d.get("phone",""),"email":d.get("email",""),"created":today()}
    db_save("customers",cid,row); return {"success":True,"customer":row}

@app.delete("/api/customers/{cid}")
def delete_cust(cid: str): db_del("customers",cid); return {"success":True}

# ═══ INVOICES ═══
@app.get("/api/invoices")
def list_inv(): return {"invoices": db_list("invoices")}

@app.post("/api/invoices")
async def create_inv(r: Request):
    d = await r.json(); labour = float(d.get("labour",0)); parts = float(d.get("parts",0))
    subtotal = labour+parts; vat = subtotal*0.15; total = subtotal+vat
    iid = str(uuid.uuid4())[:6]
    row = {"id":iid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),"description":d.get("description",""),"labour":labour,"parts":parts,"subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    db_save("invoices",iid,row); return {"success":True,"invoice":row}

@app.delete("/api/invoices/{iid}")
def delete_inv(iid: str): db_del("invoices",iid); return {"success":True}

# ═══ QUOTES ═══
@app.get("/api/quotes")
def list_quotes(): return {"quotes": db_list("quotes")}

@app.post("/api/quotes")
async def create_quote(r: Request):
    d = await r.json(); labour = float(d.get("labour",0)); parts = float(d.get("parts",0))
    subtotal = labour+parts; vat = subtotal*0.15; total = subtotal+vat
    qid = str(uuid.uuid4())[:6]
    row = {"id":qid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),"description":d.get("description",""),"labour":labour,"parts":parts,"subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    db_save("quotes",qid,row); return {"success":True,"quote":row}

@app.post("/api/quotes/{qid}/accept")
async def accept_quote(qid: str):
    q = db_get("quotes",qid)
    if not q: raise HTTPException(404,"Not found")
    iid = str(uuid.uuid4())[:6]
    inv = {"id":iid,"customer":q["customer"],"vehicle":q["vehicle"],"description":q["description"],"labour":q["labour"],"parts":q["parts"],"subtotal":q["subtotal"],"vat":q["vat"],"total":q["total"],"created":now()}
    db_save("invoices",iid,inv); db_del("quotes",qid); return {"success":True,"invoice":inv}

@app.delete("/api/quotes/{qid}")
def delete_quote(qid: str): db_del("quotes",qid); return {"success":True}

# ═══ APPOINTMENTS ═══
@app.get("/api/appointments")
def list_appts(): return {"appointments": db_list("appointments")}

@app.post("/api/appointments")
async def create_appt(r: Request):
    d = await r.json(); aid = str(uuid.uuid4())[:6]
    row = {"id":aid,"customer":d.get("customer",""),"phone":d.get("phone",""),"vehicle":d.get("vehicle",""),"service":d.get("service",""),"date":d.get("date",""),"time":d.get("time",""),"created":now()}
    db_save("appointments",aid,row); return {"success":True,"appointment":row}

@app.delete("/api/appointments/{aid}")
def delete_appt(aid: str): db_del("appointments",aid); return {"success":True}

# ═══ INVENTORY ═══
@app.get("/api/inventory")
def list_inv_items(): return {"items": db_list("inventory")}

@app.get("/api/inventory/low-stock")
def low_stock(): return {"items":[{"id":i["id"],"name":i["name"],"qty":int(i.get("qty",0)),"min":int(i.get("min_qty",5))} for i in db_list("inventory") if int(i.get("qty",0))<=int(i.get("min_qty",5))]}

@app.post("/api/inventory")
async def add_inv_item(r: Request):
    d = await r.json(); iid = str(uuid.uuid4())[:6]
    row = {"id":iid,"part_number":d.get("part_number",""),"name":d.get("name",""),"category":d.get("category",""),"qty":int(d.get("qty",0)),"min_qty":int(d.get("min_qty",5)),"cost_price":float(d.get("cost_price",0)),"sell_price":float(d.get("sell_price",0)),"supplier":d.get("supplier",""),"created":today()}
    db_save("inventory",iid,row); return {"success":True,"item":row}

@app.post("/api/inventory/{iid}/adjust")
async def adjust_inv(iid: str, r: Request):
    d = await r.json(); item = db_get("inventory",iid)
    if not item: raise HTTPException(404,"Not found")
    item["qty"] = max(0, int(item.get("qty",0))+int(d.get("delta",0)))
    db_save("inventory",iid,item); return {"success":True,"item":item}

@app.delete("/api/inventory/{iid}")
def delete_inv_item(iid: str): db_del("inventory",iid); return {"success":True}

# ═══ STAFF ═══
@app.get("/api/staff")
def list_staff(): return {"staff": db_list("staff")}

@app.post("/api/staff")
async def add_staff(r: Request):
    d = await r.json(); sid = str(uuid.uuid4())[:6]
    row = {"id":sid,"name":d.get("name",""),"role":d.get("role",""),"phone":d.get("phone",""),"email":d.get("email",""),"hourly_rate":float(d.get("hourly_rate",150)),"created":today()}
    db_save("staff",sid,row); return {"success":True,"staff":row}

@app.delete("/api/staff/{sid}")
def delete_staff(sid: str): db_del("staff",sid); return {"success":True}

# ═══ EXPENSES ═══
@app.get("/api/expenses")
def list_exp(): return {"expenses": db_list("expenses")}

@app.post("/api/expenses")
async def add_exp(r: Request):
    d = await r.json(); eid = str(uuid.uuid4())[:6]
    row = {"id":eid,"category":d.get("category","Other"),"amount":float(d.get("amount",0)),"date":d.get("date",today()),"note":d.get("note",""),"created":now()}
    db_save("expenses",eid,row); return {"success":True,"expense":row}

@app.delete("/api/expenses/{eid}")
def delete_exp(eid: str): db_del("expenses",eid); return {"success":True}

# ═══ SUPPLIERS ═══
@app.get("/api/suppliers")
def list_suppliers(): return {"suppliers": db_list("suppliers")}

@app.post("/api/suppliers")
async def add_supplier(r: Request):
    d = await r.json(); sid = str(uuid.uuid4())[:6]
    row = {"id":sid,"name":d.get("name",""),"phone":d.get("phone",""),"email":d.get("email",""),"whatsapp":d.get("whatsapp",""),"category":d.get("category",""),"account_number":d.get("account_number",""),"notes":d.get("notes",""),"created":today()}
    db_save("suppliers",sid,row); return {"success":True,"supplier":row}

@app.delete("/api/suppliers/{sid}")
def delete_supplier(sid: str): db_del("suppliers",sid); return {"success":True}

# ═══ WORKSHOP ═══
@app.get("/api/workshop")
def get_ws(): return ws_get()

@app.post("/api/workshop")
async def save_ws(r: Request):
    d = await r.json(); ws_save(d); return {"success":True,"workshop":ws_get()}

# ═══════════════════════════════════
# FRONTEND (HTML)
# ═══════════════════════════════════
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>RamsTech</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#f0f2f5;--card:#fff;--text:#1a1a2e;--text2:#6b7280;--border:#e5e7eb;--primary:#E65100;--success:#10b981;--danger:#ef4444;--warning:#f59e0b;--grad1:linear-gradient(135deg,#667eea,#764ba2);--grad-success:linear-gradient(135deg,#43e97b,#38f9d7);--grad-danger:linear-gradient(135deg,#ef4444,#f87171)}
body.dark{--bg:#0f172a;--card:#1e293b;--text:#f1f5f9;--text2:#94a3b8;--border:#334155}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,sans-serif;background:var(--bg);color:var(--text);padding-bottom:90px;transition:background .3s,color .3s}
.header{background:var(--grad1);color:white;padding:18px 16px 22px;text-align:center;position:relative;overflow:hidden;border-bottom-left-radius:26px;border-bottom-right-radius:26px;box-shadow:0 6px 24px rgba(102,126,234,.35)}
.header::before{content:'';position:absolute;top:-60%;right:-25%;width:320px;height:320px;background:radial-gradient(circle,rgba(255,255,255,.15),transparent 70%);border-radius:50%}
.header h1{font-size:21px;font-weight:800;position:relative;z-index:1}
.header p{font-size:11px;opacity:.9;margin-top:4px;position:relative;z-index:1}
.top-btns{position:absolute;right:10px;top:12px;z-index:2}
.top-btns button{background:rgba(255,255,255,.25);border:none;color:white;padding:8px 10px;border-radius:11px;font-size:15px;cursor:pointer}
.panel{display:none;padding:16px;max-width:820px;margin:0 auto;padding-bottom:100px}
.panel.active{display:block;animation:fadeSlide .35s ease}
@keyframes fadeSlide{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.panel-title{font-size:21px;font-weight:800;color:var(--primary);margin-bottom:18px}
.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{background:var(--card);border-radius:18px;padding:22px 12px;cursor:pointer;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border);transition:transform .15s}
.tile:active{transform:scale(.96)}
.tile-icon{font-size:38px;margin-bottom:8px;display:block}
.tile-label{font-size:12.5px;font-weight:700;color:var(--text)}
.card{background:var(--card);padding:16px;border-radius:18px;margin-bottom:12px;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border);animation:fadeSlide .25s ease}
.card h3{color:var(--primary);margin-bottom:10px;font-size:15px;font-weight:800}
.card p{margin:5px 0;font-size:13px;line-height:1.55}
.form-input{width:100%;padding:14px 16px;border:1.5px solid var(--border);border-radius:13px;font-size:15px;margin-bottom:10px;background:var(--card);color:var(--text);font-family:inherit}
.form-input:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 3px rgba(230,81,0,.1)}
textarea.form-input{resize:vertical;min-height:60px}
.btn{width:100%;padding:15px;border:none;border-radius:13px;font-size:15px;font-weight:800;cursor:pointer;margin-bottom:10px;background:var(--grad1);color:white;box-shadow:0 4px 14px rgba(102,126,234,.28);transition:transform .15s;display:flex;align-items:center;justify-content:center;gap:8px}
.btn:active{transform:scale(.97)}
.btn-green{background:var(--grad-success);box-shadow:0 4px 14px rgba(67,233,123,.28)}
.btn-dark{background:linear-gradient(135deg,#4b5563,#1f2937)}
.btn-primary{background:linear-gradient(135deg,#E65100,#FF9800);box-shadow:0 4px 14px rgba(230,81,0,.28)}
.btn-sm{padding:8px 13px;border:none;border-radius:9px;font-size:12px;font-weight:700;cursor:pointer;margin-right:5px;margin-bottom:4px;background:var(--primary);color:white}
.btn-sm:active{transform:scale(.92)}
.btn-sm.green{background:var(--success)}.btn-sm.red{background:var(--danger)}.btn-sm.blue{background:#3b82f6}.btn-sm.gray{background:#6b7280}.btn-sm.wa{background:#25D366}
.badge{display:inline-block;padding:3px 10px;border-radius:7px;font-size:11px;font-weight:800;color:white;margin-left:6px}
.badge.high,.badge.critical,.badge.warn{background:var(--danger)}
.badge.medium,.badge.inprogress{background:var(--warning)}
.badge.low,.badge.ok,.badge.completed,.badge.active{background:var(--success)}
.badge.new,.badge.expired{background:#6b7280}
.list-item{padding:9px 0;border-bottom:1px solid var(--border);font-size:13px;line-height:1.5}
.list-item:last-child{border-bottom:none}
.chat-box{background:var(--card);border-radius:18px;padding:14px;height:calc(100vh - 300px);overflow-y:auto;margin-bottom:12px;border:1px solid var(--border)}
.msg{padding:12px 16px;margin:8px 0;border-radius:16px;max-width:85%;word-wrap:break-word;font-size:14px;line-height:1.5;animation:fadeSlide .2s ease}
.msg.user{background:var(--grad1);color:white;margin-left:auto;border-bottom-right-radius:4px}
.msg.ai{background:#f9fafb;border-bottom-left-radius:4px;border:1px solid var(--border)}
body.dark .msg.ai{background:#334155}
.input-row{display:flex;gap:8px;align-items:center}
.input-row input{flex:1;padding:14px 18px;border:1.5px solid var(--border);border-radius:26px;font-size:15px;outline:none;background:var(--card);color:var(--text)}
.input-row input:focus{border-color:var(--primary)}
.input-row button{padding:14px 15px;background:var(--grad1);color:white;border:none;border-radius:50%;font-weight:bold;cursor:pointer;font-size:16px}
.mic-btn{background:var(--grad-success)!important}
.mic-btn.recording{background:var(--grad-danger)!important;animation:pulse 1.2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--border);display:flex;padding:8px 4px 10px;z-index:100;box-shadow:0 -4px 20px rgba(0,0,0,.06)}
.bnav{flex:1;text-align:center;padding:6px 4px;cursor:pointer;border-radius:12px}
.bnav.active{background:rgba(230,81,0,.08)}
.bnav-icon{font-size:20px;display:block;margin-bottom:3px}
.bnav-label{font-size:9px;font-weight:800;color:var(--text2);text-transform:uppercase;letter-spacing:.5px}
.bnav.active .bnav-label{color:var(--primary)}
.status-online{background:var(--grad-success);color:white;padding:11px 16px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700}
.status-offline{background:var(--grad-danger);color:white;padding:11px 16px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700}
.status-checking{background:linear-gradient(135deg,#f59e0b,#fbbf24);color:white;padding:11px 16px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700;animation:pulse 1.5s infinite}
.empty{text-align:center;padding:40px 20px;color:var(--text2)}
.empty-icon{font-size:64px;margin-bottom:12px;display:block;opacity:.5}
.empty-title{font-size:15px;font-weight:700;color:var(--text);margin-bottom:6px}
.empty-text{font-size:13px;line-height:1.5}
.skeleton{background:linear-gradient(90deg,var(--border) 25%,rgba(255,255,255,.4) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.5s infinite;border-radius:8px}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.skeleton-card{background:var(--card);padding:16px;border-radius:18px;margin-bottom:12px;border:1px solid var(--border)}
.skeleton-line{height:12px;margin-bottom:10px;border-radius:6px}
.skeleton-line.title{width:60%;height:16px}
.skeleton-line.short{width:40%}
#toast-container{position:fixed;top:16px;left:16px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:8px;pointer-events:none}
.toast{padding:14px 18px;border-radius:14px;color:white;font-size:14px;font-weight:600;box-shadow:0 8px 24px rgba(0,0,0,.25);animation:toastIn .3s ease;pointer-events:auto;max-width:500px;margin:0 auto;width:100%;display:flex;align-items:center;gap:10px}
@keyframes toastIn{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}
.toast.out{animation:toastOut .3s ease forwards}
@keyframes toastOut{to{opacity:0;transform:translateY(-20px)}}
.toast.success{background:var(--grad-success)}
.toast.error{background:var(--grad-danger)}
.toast.info{background:var(--grad1)}
.toast.warning{background:linear-gradient(135deg,#f59e0b,#fbbf24)}
.img-preview{width:100%;border-radius:16px;margin-bottom:12px}
.swatch{height:100px;border-radius:16px;border:2px solid var(--border);margin-bottom:12px}
.photo-row{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;margin-bottom:10px}
.photo-thumb{width:88px;height:88px;object-fit:cover;border-radius:12px;border:2px solid var(--border);flex-shrink:0}
.torque-table{width:100%;border-collapse:collapse;background:var(--card);border-radius:14px;overflow:hidden;font-size:12px;margin-bottom:12px}
.torque-table th{background:var(--grad1);color:white;padding:11px 9px;text-align:left;font-weight:700;font-size:11px}
.torque-table td{padding:11px 9px;border-bottom:1px solid var(--border);color:var(--text)}
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat-card{background:var(--card);padding:16px 12px;border-radius:18px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border);position:relative;overflow:hidden}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#E65100,#FF9800)}
.stat-card.blue::before{background:linear-gradient(90deg,#3b82f6,#60a5fa)}
.stat-card.green::before{background:var(--grad-success)}
.stat-card.red::before{background:var(--grad-danger)}
.stat-card .num{font-size:23px;font-weight:800;color:var(--primary)}
.stat-card.green .num{color:var(--success)}.stat-card.red .num{color:var(--danger)}.stat-card.blue .num{color:#3b82f6}
.stat-card .lbl{font-size:10px;color:var(--text2);margin-top:5px;font-weight:700;text-transform:uppercase}
canvas{max-height:220px}
@media print{.header,.bottom-nav,.no-print,button,.btn,.btn-sm,#toast-container{display:none!important}.panel{display:block!important}.panel:not(.active){display:none!important}body{background:white;color:black}}
</style>
</head>
<body>

<div id="toast-container"></div>

<div class="header">
<h1><span id="logoDisplay">🔧</span> <span id="wsName">RAMSTECH</span></h1>
<p id="wsSub">AI Workshop Assistant</p>
<div class="top-btns"><button onclick="toggleTheme()" id="themeBtn">🌙</button></div>
</div>

<!-- HOME -->
<div id="home" class="panel active">
<div class="card" id="statusCard">
  <div id="status">
    <div style="text-align:center;padding:20px">
      <div style="font-size:40px;margin-bottom:12px">⏳</div>
      <div style="font-weight:700;font-size:15px;margin-bottom:6px">Connecting to server...</div>
      <div style="font-size:12px;color:var(--text2);margin-bottom:12px" id="statusMsg">
        Render free tier may take up to 60 seconds to wake up
      </div>
      <div style="height:6px;background:var(--border);border-radius:3px;overflow:hidden">
        <div id="progressBar" style="height:100%;width:0%;background:var(--grad1);transition:width .3s;border-radius:3px"></div>
      </div>
      <div style="font-size:11px;color:var(--text2);margin-top:10px" id="attemptMsg">Attempt 1 of 3</div>
    </div>
  </div>
</div>
<div class="tile-grid" id="homeGrid" style="display:none"></div>
</div>

<!-- DASHBOARD -->
<div id="dashboard" class="panel">
<div class="panel-title">📊 Dashboard</div>
<div id="dashStats"></div>
<div class="card"><h3>💰 Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>📋 Job Status</h3><canvas id="jobChart"></canvas></div>
<div class="card"><h3>⚠️ Low Stock</h3><div id="dashLowStock"></div></div>
</div>

<!-- ANALYTICS -->
<div id="analytics" class="panel">
<div class="panel-title">📈 Analytics</div>
<div id="analyticsContent"></div>
</div>

<!-- WARRANTY -->
<div id="warranty" class="panel">
<div class="panel-title">🎁 Warranty Tracker</div>
<div id="warrantyList"></div>
</div>

<!-- TAX -->
<div id="tax" class="panel">
<div class="panel-title">🧾 Tax & Reports</div>
<div class="card">
<h3>📅 Tax Report Period</h3>
<input class="form-input" id="taxFrom" type="date">
<input class="form-input" id="taxTo" type="date">
<button class="btn btn-dark" onclick="downloadTax()">📥 Download CSV</button>
</div>
</div>

<!-- VIN -->
<div id="vin" class="panel">
<div class="panel-title">🔍 VIN Decoder</div>
<div class="card">
<input class="form-input" id="vinInput" placeholder="17-character VIN" maxlength="17" style="text-transform:uppercase">
<button class="btn btn-green" onclick="decodeVin()">🔍 Decode</button>
<div id="vinResult"></div>
</div>
</div>

<!-- PHOTO -->
<div id="photo" class="panel">
<div class="panel-title">📸 Photo Diagnosis</div>
<div class="card">
<input class="form-input" id="photoVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)">
<div id="photoPreview"></div>
<button class="btn btn-green" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze Photo</button>
<div id="photoResult"></div>
</div>
</div>

<!-- PAINT -->
<div id="paint" class="panel">
<div class="panel-title">🎨 Paint Match</div>
<div class="card">
<input class="form-input" id="paintVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)">
<div id="paintPreview"></div>
<button class="btn btn-green" id="paintBtn" onclick="matchPaint()">🎨 Match Colour</button>
<div id="paintResult"></div>
</div>
</div>

<!-- SPECS -->
<div id="specs" class="panel"><div class="panel-title">🔧 Vehicle Specs</div><input type="text" class="form-input" id="specsSearch" placeholder="🔍 Search..." oninput="filterSpecs()"><div id="specsList"></div></div>
<!-- INTERVALS -->
<div id="intervals" class="panel"><div class="panel-title">⏰ Service Intervals</div><div id="intervalList"></div></div>
<!-- BOOK TIME -->
<div id="booktime" class="panel"><div class="panel-title">⏱️ Book Time</div><div id="bookList"></div></div>
<!-- SUPPLIERS -->
<div id="suppliers" class="panel">
<div class="panel-title">📞 Suppliers</div>
<button class="btn btn-green" onclick="showForm('supplierForm')">+ Add Supplier</button>
<div id="supplierForm" style="display:none">
<div class="card">
<input class="form-input" id="supName" placeholder="Name">
<input class="form-input" id="supPhone" placeholder="Phone">
<input class="form-input" id="supEmail" placeholder="Email">
<input class="form-input" id="supWhatsapp" placeholder="WhatsApp">
<input class="form-input" id="supCategory" placeholder="Category">
<input class="form-input" id="supAccount" placeholder="Account #">
<button class="btn btn-green" onclick="addSupplier()">Save</button>
<button class="btn btn-dark" onclick="hideForm('supplierForm')">Cancel</button>
</div>
</div>
<div id="supplierList"></div>
</div>

<!-- CHAT -->
<div id="chat" class="panel">
<div class="panel-title">🤖 AI Assistant</div>
<div class="chat-box" id="chatBox"><div class="msg ai">Hi! Ask me about repairs.</div></div>
<div class="input-row">
<input type="text" id="chatInput" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendMsg()">
<button class="mic-btn" id="micBtn" onclick="toggleMic()">🎤</button>
<button onclick="sendMsg()">➤</button>
</div>
</div>

<!-- CODES -->
<div id="codes" class="panel"><div class="panel-title">📟 Fault Codes</div><input type="text" class="form-input" id="codeSearch" placeholder="🔍 Search..." oninput="searchCodes()"><div id="codeResults"></div></div>

<!-- JOBS -->
<div id="jobs" class="panel">
<div class="panel-title">📋 Jobs</div>
<button class="btn btn-green" onclick="showForm('jobForm')">+ New Job</button>
<div id="jobForm" style="display:none">
<div class="card">
<input class="form-input" id="jCustomer" placeholder="Customer name">
<input class="form-input" id="jPhone" placeholder="Phone">
<input class="form-input" id="jVehicle" placeholder="Vehicle">
<input class="form-input" id="jReg" placeholder="Registration">
<textarea class="form-input" id="jComplaint" placeholder="Complaint" rows="2"></textarea>
<select class="form-input" id="jAssigned"><option value="">— Assign —</option></select>
<input class="form-input" id="jWarranty" type="number" placeholder="Warranty months" value="6">
<button class="btn btn-green" onclick="createJob()">Save</button>
<button class="btn btn-dark" onclick="hideForm('jobForm')">Cancel</button>
</div>
</div>
<div id="jobList"></div>
</div>

<!-- QUOTES -->
<div id="quotes" class="panel">
<div class="panel-title">💬 Quotes</div>
<button class="btn btn-green" onclick="showForm('quoteForm')">+ New Quote</button>
<div id="quoteForm" style="display:none">
<div class="card">
<input class="form-input" id="qCustomer" placeholder="Customer">
<input class="form-input" id="qVehicle" placeholder="Vehicle">
<textarea class="form-input" id="qDesc" placeholder="Description" rows="2"></textarea>
<input class="form-input" id="qLabour" type="number" placeholder="Labour R" value="0">
<input class="form-input" id="qParts" type="number" placeholder="Parts R" value="0">
<button class="btn btn-green" onclick="createQuote()">Save</button>
<button class="btn btn-dark" onclick="hideForm('quoteForm')">Cancel</button>
</div>
</div>
<div id="quoteList"></div>
</div>

<!-- APPOINTMENTS -->
<div id="appointments" class="panel">
<div class="panel-title">📅 Appointments</div>
<button class="btn btn-green" onclick="showForm('apptForm')">+ New Appointment</button>
<div id="apptForm" style="display:none">
<div class="card">
<input class="form-input" id="aCustomer" placeholder="Customer">
<input class="form-input" id="aPhone" placeholder="Phone">
<input class="form-input" id="aVehicle" placeholder="Vehicle">
<input class="form-input" id="aService" placeholder="Service">
<input class="form-input" id="aDate" type="date">
<input class="form-input" id="aTime" type="time">
<button class="btn btn-green" onclick="createAppt()">Book</button>
<button class="btn btn-dark" onclick="hideForm('apptForm')">Cancel</button>
</div>
</div>
<div id="apptList"></div>
</div>

<!-- CUSTOMERS -->
<div id="customers" class="panel">
<div class="panel-title">👥 Customers</div>
<button class="btn btn-green" onclick="showForm('custForm')">+ New Customer</button>
<div id="custForm" style="display:none">
<div class="card">
<input class="form-input" id="cName" placeholder="Name">
<input class="form-input" id="cPhone" placeholder="Phone">
<input class="form-input" id="cEmail" placeholder="Email">
<button class="btn btn-green" onclick="createCustomer()">Save</button>
<button class="btn btn-dark" onclick="hideForm('custForm')">Cancel</button>
</div>
</div>
<div id="custList"></div>
</div>

<!-- INVOICES -->
<div id="invoices" class="panel">
<div class="panel-title">💰 Invoices</div>
<button class="btn btn-green" onclick="showForm('invForm')">+ New Invoice</button>
<div id="invForm" style="display:none">
<div class="card">
<input class="form-input" id="iCustomer" placeholder="Customer">
<input class="form-input" id="iVehicle" placeholder="Vehicle">
<input class="form-input" id="iDesc" placeholder="Description">
<input class="form-input" id="iLabour" type="number" placeholder="Labour R">
<input class="form-input" id="iParts" type="number" placeholder="Parts R">
<button class="btn btn-green" onclick="createInvoice()">Save</button>
<button class="btn btn-dark" onclick="hideForm('invForm')">Cancel</button>
</div>
</div>
<div id="invList"></div>
</div>

<!-- INVENTORY -->
<div id="inventory" class="panel">
<div class="panel-title">📦 Inventory</div>
<button class="btn btn-green" onclick="showForm('invItemForm')">+ Add Item</button>
<div id="invItemForm" style="display:none">
<div class="card">
<input class="form-input" id="pNumber" placeholder="Part number">
<input class="form-input" id="pName" placeholder="Name">
<input class="form-input" id="pCategory" placeholder="Category">
<input class="form-input" id="pQty" type="number" placeholder="Qty">
<input class="form-input" id="pMinQty" type="number" placeholder="Min qty" value="5">
<input class="form-input" id="pCost" type="number" placeholder="Cost R">
<input class="form-input" id="pSell" type="number" placeholder="Sell R">
<input class="form-input" id="pSupplier" placeholder="Supplier">
<button class="btn btn-green" onclick="addInventory()">Save</button>
<button class="btn btn-dark" onclick="hideForm('invItemForm')">Cancel</button>
</div>
</div>
<div id="inventoryList"></div>
</div>

<!-- STAFF -->
<div id="staff" class="panel">
<div class="panel-title">👷 Staff</div>
<button class="btn btn-green" onclick="showForm('staffForm')">+ Add Staff</button>
<div id="staffForm" style="display:none">
<div class="card">
<input class="form-input" id="stName" placeholder="Name">
<input class="form-input" id="stRole" placeholder="Role">
<input class="form-input" id="stPhone" placeholder="Phone">
<input class="form-input" id="stEmail" placeholder="Email">
<input class="form-input" id="stRate" type="number" placeholder="Hourly R" value="150">
<button class="btn btn-green" onclick="addStaff()">Save</button>
<button class="btn btn-dark" onclick="hideForm('staffForm')">Cancel</button>
</div>
</div>
<div id="staffList"></div>
</div>

<!-- EXPENSES -->
<div id="expenses" class="panel">
<div class="panel-title">💸 Expenses</div>
<button class="btn btn-green" onclick="showForm('expForm')">+ Add Expense</button>
<div id="expForm" style="display:none">
<div class="card">
<select class="form-input" id="exCat"><option>Rent</option><option>Utilities</option><option>Tools</option><option>Parts</option><option>Salaries</option><option>Fuel</option><option>Other</option></select>
<input class="form-input" id="exAmount" type="number" placeholder="Amount R">
<input class="form-input" id="exDate" type="date">
<textarea class="form-input" id="exNote" placeholder="Note" rows="2"></textarea>
<button class="btn btn-green" onclick="addExpense()">Save</button>
<button class="btn btn-dark" onclick="hideForm('expForm')">Cancel</button>
</div>
</div>
<div id="expenseList"></div>
</div>

<!-- TORQUE -->
<div id="torque" class="panel"><div class="panel-title">⚙️ Torque Specs</div><input type="text" class="form-input" id="torqueSearch" placeholder="🔍 Search..." oninput="filterTorque()"><div id="torqueTable"></div><h3 style="margin:16px 0 8px;font-size:14px;color:var(--text2)">Sequences</h3><div id="torqueSeq"></div></div>

<!-- BOLT CALC -->
<div id="boltcalc" class="panel">
<div class="panel-title">🔧 Bolt Calculator</div>
<div class="card">
<select class="form-input" id="boltSize"><option>M6</option><option>M8</option><option selected>M10</option><option>M12</option><option>M14</option><option>M16</option><option>M20</option></select>
<select class="form-input" id="boltGrade"><option>8.8</option><option selected>10.9</option><option>12.9</option></select>
<select class="form-input" id="boltCondition"><option value="dry">Dry</option><option value="oiled">Oiled</option><option value="moly">Moly</option></select>
<button class="btn" onclick="calcTorque()">Calculate</button>
<div id="boltResult"></div>
</div>
</div>

<!-- BULBS/BATT/TYRES/WIRING/OBD -->
<div id="bulbs" class="panel"><div class="panel-title">💡 Bulbs</div><div id="bulbList"></div></div>
<div id="batteries" class="panel"><div class="panel-title">🔋 Batteries</div><div id="battList"></div></div>
<div id="tyres" class="panel"><div class="panel-title">🛞 Tyres</div><div id="tyreList"></div></div>
<div id="wiring" class="panel"><div class="panel-title">🔌 Wiring</div><div id="wiringList"></div></div>
<div id="obd" class="panel"><div class="panel-title">⚡ OBD-II PIDs</div><div id="obdList"></div></div>

<!-- SETTINGS -->
<div id="settings" class="panel">
<div class="panel-title">⚙️ Settings</div>
<div class="card">
<h3>🏢 Workshop</h3>
<input class="form-input" id="sLogo" placeholder="🔧" maxlength="4">
<input class="form-input" id="sName" placeholder="Workshop name">
<input class="form-input" id="sPhone" placeholder="Phone">
<input class="form-input" id="sEmail" placeholder="Email">
<input class="form-input" id="sAddress" placeholder="Address">
<input class="form-input" id="sRate" type="number" placeholder="Labour R/hr">
<h3 style="margin-top:16px">🧾 Business</h3>
<input class="form-input" id="sVat" placeholder="VAT number">
<input class="form-input" id="sCompany" placeholder="Company reg">
<input class="form-input" id="sBank" placeholder="Bank details">
<h3 style="margin-top:16px">📜 Terms</h3>
<textarea class="form-input" id="sTerms" rows="4"></textarea>
<button class="btn btn-green" onclick="saveSettings()">Save All</button>
</div>
</div>

<!-- BOTTOM NAV -->
<div class="bottom-nav no-print">
<div class="bnav active" onclick="showTab('home',this)"><div class="bnav-icon">🏠</div><div class="bnav-label">Home</div></div>
<div class="bnav" onclick="showTab('chat',this)"><div class="bnav-icon">🤖</div><div class="bnav-label">AI</div></div>
<div class="bnav" onclick="showTab('jobs',this)"><div class="bnav-icon">📋</div><div class="bnav-label">Jobs</div></div>
<div class="bnav" onclick="showTab('specs',this)"><div class="bnav-icon">🔧</div><div class="bnav-label">Specs</div></div>
<div class="bnav" onclick="showTab('settings',this)"><div class="bnav-icon">⚙️</div><div class="bnav-label">More</div></div>
</div>

<script>
// ═══════════════════════════════════
// ⚡ SERVER WAKE-UP WITH RETRY LOGIC
// ═══════════════════════════════════
// This is the key fix - retries 3 times over 60 seconds
async function checkStatus(){
  const statusDiv = document.getElementById('status');
  const progressBar = document.getElementById('progressBar');
  const attemptMsg = document.getElementById('attemptMsg');
  const statusMsg = document.getElementById('statusMsg');
  
  const MAX_ATTEMPTS = 3;
  const TIMEOUT_PER_ATTEMPT = 20000; // 20 seconds each
  const DELAY_BETWEEN = 2000; // 2 seconds between retries
  
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++){
    // Update UI
    if (progressBar) progressBar.style.width = ((attempt - 1) / MAX_ATTEMPTS * 100) + '%';
    if (attemptMsg) attemptMsg.textContent = 'Attempt ' + attempt + ' of ' + MAX_ATTEMPTS;
    if (statusMsg){
      if (attempt === 1) statusMsg.textContent = 'Render free tier may take up to 60 seconds to wake up';
      else if (attempt === 2) statusMsg.textContent = 'Still waking up... hang in there';
      else statusMsg.textContent = 'Almost there... one more try';
    }
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_PER_ATTEMPT);
      
      const r = await fetch('/health', { signal: controller.signal, cache: 'no-store' });
      clearTimeout(timeoutId);
      
      if (r.ok){
        const d = await r.json();
        if (progressBar) progressBar.style.width = '100%';
        
        // Success! Show tiles
        document.getElementById('homeGrid').style.display = 'grid';
        statusDiv.innerHTML = '<span class="status-online">✓ Server Connected</span>' +
          '<span style="margin-left:8px;font-size:12px;color:var(--text2)">' +
          (DB_READY_TXT || '') + '</span>';
        toast('Connected ✓', 'success');
        return true;
      }
    } catch (e){
      // Silent fail - try again
      console.log('Attempt ' + attempt + ' failed:', e.message);
    }
    
    // Wait before next attempt (but not after last)
    if (attempt < MAX_ATTEMPTS){
      await new Promise(r => setTimeout(r, DELAY_BETWEEN));
    }
  }
  
  // All attempts failed - show error screen
  if (progressBar) progressBar.style.width = '100%';
  statusDiv.innerHTML = 
    '<div style="text-align:center;padding:20px">' +
    '<div style="font-size:40px;margin-bottom:12px">😴</div>' +
    '<div style="font-weight:700;font-size:15px;margin-bottom:6px">Server is sleeping</div>' +
    '<div style="font-size:12px;color:var(--text2);margin-bottom:16px">Render free tier sleeps after 15 minutes of inactivity. It takes 30-60 seconds to wake up.</div>' +
    '<button class="btn btn-primary" onclick="retryConnection()" style="max-width:280px;margin:0 auto">🔄 Try Again</button>' +
    '</div>';
  toast('Server is waking up. Please try again.', 'warning', 5000);
  return false;
}

let DB_READY_TXT = '';
async function retryConnection(){
  const statusDiv = document.getElementById('status');
  statusDiv.innerHTML = '<div style="text-align:center;padding:20px"><div style="font-size:40px;margin-bottom:12px">⏳</div><div style="font-weight:700;font-size:15px;margin-bottom:6px">Connecting...</div><div style="height:6px;background:var(--border);border-radius:3px;overflow:hidden;margin-top:12px"><div id="progressBar" style="height:100%;width:0%;background:var(--grad1);transition:width .3s;border-radius:3px"></div></div><div style="font-size:11px;color:var(--text2);margin-top:10px" id="attemptMsg">Starting...</div></div>';
  await checkStatus();
}

// Start checking immediately
checkStatus();

// Also re-check every 5 min when app is opened (in case it went to sleep)
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && !isConnected) checkStatus();
});

let isConnected = false;

// ═══════════════════════════════════
// HOME TILES
// ═══════════════════════════════════
const TILES = [
  ['dashboard','📊','Dashboard'],['chat','🤖','AI Chat'],['codes','📟','Fault Codes'],
  ['vin','🔍','VIN'],['photo','📸','Photo Diag'],['paint','🎨','Paint'],
  ['specs','🔧','Vehicle Specs'],['intervals','⏰','Intervals'],['booktime','⏱️','Book Time'],
  ['suppliers','📞','Suppliers'],['jobs','📋','Jobs'],['quotes','💬','Quotes'],
  ['appointments','📅','Appts'],['customers','👥','Customers'],['invoices','💰','Invoices'],
  ['inventory','📦','Inventory'],['staff','👷','Staff'],['expenses','💸','Expenses'],
  ['analytics','📈','Analytics'],['warranty','🎁','Warranty'],['tax','🧾','Tax'],
  ['torque','⚙️','Torque'],['boltcalc','🔧','Bolt Calc'],['bulbs','💡','Bulbs'],
  ['batteries','🔋','Batteries'],['tyres','🛞','Tyres'],['wiring','🔌','Wiring'],
  ['obd','⚡','OBD-II'],['settings','⚙️','Settings']
];
document.getElementById('homeGrid').innerHTML = TILES.map(t =>
  '<div class="tile" onclick="showTab(\'' + t[0] + '\')"><span class="tile-icon">' + t[1] + '</span><div class="tile-label">' + t[2] + '</div></div>'
).join('');

// ═══════════════════════════════════
// TAB SWITCHING
// ═══════════════════════════════════
function showTab(name, el){
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.bnav').forEach(t => t.classList.remove('active'));
  const panel = document.getElementById(name);
  if (panel) panel.classList.add('active');
  if (el && el.classList) el.classList.add('active');
  window.scrollTo(0,0);
  const loaders = {
    dashboard:loadDash,analytics:loadAnalytics,warranty:loadWarranty,tax:loadTax,
    specs:loadSpecs,intervals:loadIntervals,booktime:loadBookTime,suppliers:loadSuppliers,
    jobs:()=>{loadJobs();loadStaffDropdown();},quotes:loadQuotes,appointments:loadAppts,
    customers:loadCust,invoices:loadInv,inventory:loadInventory,staff:loadStaff,
    expenses:loadExpenses,torque:loadTorque,bulbs:loadBulbs,batteries:loadBatt,
    tyres:loadTyre,wiring:loadWiring,obd:loadOBD,settings:loadSettings,
    codes:()=>{if(!document.getElementById('codeResults').dataset.loaded)searchCodes();}
  };
  if (loaders[name]) try{loaders[name]();}catch(e){console.error(e);}
}

// ═══════════════════════════════════
// HELPERS
// ═══════════════════════════════════
function toggleTheme(){
  document.body.classList.toggle('dark');
  const d = document.body.classList.contains('dark');
  localStorage.setItem('theme', d ? 'dark' : 'light');
  document.getElementById('themeBtn').textContent = d ? '☀️' : '🌙';
}
if (localStorage.getItem('theme') === 'dark'){
  document.body.classList.add('dark');
  document.getElementById('themeBtn').textContent = '☀️';
}
function showForm(id){document.getElementById(id).style.display='block';}
function hideForm(id){document.getElementById(id).style.display='none';}
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML;}
async function jget(u){const r=await fetch(u);return r.json();}
async function jpost(u,b){const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json();}
async function jput(u,b){const r=await fetch(u,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json();}
function toast(msg, type, duration){
  type = type || 'info'; duration = duration || 3000;
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  const icons = {success:'✓', error:'✕', info:'ℹ', warning:'⚠'};
  t.innerHTML = '<span style="font-size:20px">' + icons[type] + '</span><span>' + msg + '</span>';
  c.appendChild(t);
  setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 300); }, duration);
}
function emptyState(icon, title, text){
  return '<div class="empty"><span class="empty-icon">' + icon + '</span><div class="empty-title">' + title + '</div><div class="empty-text">' + text + '</div></div>';
}
function skeleton(){
  return '<div class="skeleton-card"><div class="skeleton skeleton-line title"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div></div>';
}
function compressImage(file, maxWidth, quality){
  return new Promise(resolve => {
    const reader = new FileReader();
    reader.onload = e => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let { width, height } = img;
        if (width > maxWidth){ height = (height * maxWidth) / width; width = maxWidth; }
        canvas.width = width; canvas.height = height;
        canvas.getContext('2d').drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL('image/jpeg', quality));
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// ═══════════════════════════════════
// CHAT
// ═══════════════════════════════════
let rec = null, isRec = false;
function toggleMic(){
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)){ toast('Voice not supported', 'warning'); return; }
  if (!rec){
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    rec = new SR(); rec.lang = 'en-ZA';
    rec.onresult = e => { document.getElementById('chatInput').value = e.results[0][0].transcript; resetMic(); sendMsg(); };
    rec.onerror = resetMic; rec.onend = resetMic;
  }
  function resetMic(){ isRec = false; document.getElementById('micBtn').classList.remove('recording'); document.getElementById('micBtn').textContent = '🎤'; }
  if (isRec){ rec.stop(); resetMic(); }
  else { try { rec.start(); isRec = true; document.getElementById('micBtn').classList.add('recording'); document.getElementById('micBtn').textContent = '⏹'; } catch(e){ toast(e.message, 'error'); } }
}
async function sendMsg(){
  const i = document.getElementById('chatInput');
  const m = i.value.trim(); if (!m) return;
  const b = document.getElementById('chatBox');
  b.innerHTML += '<div class="msg user">' + esc(m) + '</div>';
  i.value = ''; b.scrollTop = b.scrollHeight;
  b.innerHTML += '<div class="msg ai" id="typ">Thinking...</div>'; b.scrollTop = b.scrollHeight;
  try { const d = await jpost('/api/chat', {message: m}); document.getElementById('typ').outerHTML = '<div class="msg ai">' + esc(d.reply) + '</div>'; }
  catch(e){ document.getElementById('typ').outerHTML = '<div class="msg ai">Error</div>'; }
  b.scrollTop = b.scrollHeight;
}

// ═══════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════
let rC = null, jC = null;
async function loadDash(){
  try {
    const d = await jget('/api/stats');
    document.getElementById('dashStats').innerHTML = '<div class="stats-row">' +
      '<div class="stat-card blue"><div class="num">' + d.jobs_total + '</div><div class="lbl">Jobs</div></div>' +
      '<div class="stat-card"><div class="num">' + d.jobs_open + '</div><div class="lbl">Open</div></div>' +
      '<div class="stat-card green"><div class="num">' + d.jobs_completed + '</div><div class="lbl">Done</div></div>' +
      '<div class="stat-card"><div class="num">' + d.customers + '</div><div class="lbl">Customers</div></div>' +
      '<div class="stat-card green"><div class="num">R' + d.revenue + '</div><div class="lbl">Revenue</div></div>' +
      '<div class="stat-card red"><div class="num">R' + d.expenses + '</div><div class="lbl">Expenses</div></div></div>';
    if (rC) rC.destroy();
    const c1 = document.getElementById('revenueChart');
    if (c1) rC = new Chart(c1, {type:'line',data:{labels:d.revenue_labels,datasets:[{data:d.revenue_data,borderColor:'#667eea',backgroundColor:'rgba(102,126,234,.15)',tension:.4,fill:true,borderWidth:3}]},options:{responsive:true,plugins:{legend:{display:false}}}});
    if (jC) jC.destroy();
    const c2 = document.getElementById('jobChart');
    if (c2) jC = new Chart(c2, {type:'doughnut',data:{labels:['New','Progress','Done'],datasets:[{data:[d.jobs_new,d.jobs_progress,d.jobs_completed],backgroundColor:['#6b7280','#f59e0b','#10b981']}]},options:{responsive:true,plugins:{legend:{position:'bottom'}}}});
    const ls = await jget('/api/inventory/low-stock');
    document.getElementById('dashLowStock').innerHTML = ls.items.length ? ls.items.map(i => '<div class="list-item">⚠️ <strong>' + esc(i.name) + '</strong> — ' + i.qty + ' left</div>').join('') : '<p style="color:var(--text2)">✓ All stock OK</p>';
  } catch(e){ toast('Failed to load', 'error'); }
}

// ═══════════════════════════════════
// ANALYTICS
// ═══════════════════════════════════
async function loadAnalytics(){
  try {
    const d = await jget('/api/analytics');
    let h = '<div class="stats-row">' +
      '<div class="stat-card blue"><div class="num">R' + d.avg_invoice.toFixed(0) + '</div><div class="lbl">Avg Inv</div></div>' +
      '<div class="stat-card green"><div class="num">R' + d.total_revenue.toFixed(0) + '</div><div class="lbl">Revenue</div></div></div>';
    if (d.top_services.length){ h += '<div class="card"><h3>🔥 Top Jobs</h3>'; d.top_services.forEach(s => { h += '<div class="list-item"><strong>' + esc(s.name) + '</strong> — ' + s.count + '×</div>'; }); h += '</div>'; }
    if (d.top_customers.length){ h += '<div class="card"><h3>⭐ Customers</h3>'; d.top_customers.forEach(x => { h += '<div class="list-item"><strong>' + esc(x.name) + '</strong> — R' + x.total.toFixed(0) + '</div>'; }); h += '</div>'; }
    document.getElementById('analyticsContent').innerHTML = h;
  } catch(e){ toast('Failed', 'error'); }
}

// ═══════════════════════════════════
// WARRANTY
// ═══════════════════════════════════
async function loadWarranty(){
  const c = document.getElementById('warrantyList'); c.innerHTML = skeleton();
  try {
    const d = await jget('/api/warranty');
    c.innerHTML = d.warranties.length ? d.warranties.map(w => {
      const cls = w.status === 'active' ? 'active' : 'expired';
      return '<div class="card"><h3>🎁 ' + esc(w.vehicle) + ' <span class="badge ' + cls + '">' + w.status.toUpperCase() + '</span></h3>' +
        '<p><strong>' + esc(w.customer) + '</strong></p>' +
        '<div class="list-item">Expires: <strong>' + esc(w.expiry) + '</strong></div>' +
        '<div class="list-item">' + (w.days_left > 0 ? w.days_left + ' days remaining' : 'Expired') + '</div></div>';
    }).join('') : emptyState('🎁','No warranties','Complete a job with warranty to see it here.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load.'); }
}

// ═══════════════════════════════════
// TAX
// ═══════════════════════════════════
async function loadTax(){
  const n = new Date(); const f = new Date(n.getFullYear(), n.getMonth(), 1);
  document.getElementById('taxFrom').value = f.toISOString().slice(0,10);
  document.getElementById('taxTo').value = n.toISOString().slice(0,10);
}
function downloadTax(){
  const f = document.getElementById('taxFrom').value;
  const t = document.getElementById('taxTo').value;
  if (!f || !t){ toast('Select dates', 'warning'); return; }
  window.location.href = '/api/export/tax?from_date=' + f + '&to_date=' + t;
  toast('Download started', 'success');
}

// ═══════════════════════════════════
// VIN
// ═══════════════════════════════════
async function decodeVin(){
  const vin = document.getElementById('vinInput').value.trim().toUpperCase();
  const c = document.getElementById('vinResult');
  if (vin.length !== 17){ toast('VIN must be 17 chars', 'warning'); return; }
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/vin/' + vin);
    if (d.detail){ c.innerHTML = ''; toast(d.detail, 'error'); return; }
    c.innerHTML = '<div class="card"><h3>🔍 Info</h3>' +
      '<div class="list-item"><strong>VIN:</strong> ' + d.vin + '</div>' +
      '<div class="list-item"><strong>Manufacturer:</strong> ' + d.manufacturer + '</div>' +
      '<div class="list-item"><strong>Country:</strong> ' + d.country + '</div>' +
      '<div class="list-item"><strong>Year:</strong> ' + d.year + '</div></div>';
  } catch(e){ c.innerHTML = ''; toast('Failed', 'error'); }
}

// ═══════════════════════════════════
// PHOTO
// ═══════════════════════════════════
let diagB64 = '';
async function previewDiag(e){
  const f = e.target.files[0]; if (!f) return;
  diagB64 = await compressImage(f, 1200, 0.75);
  document.getElementById('photoPreview').innerHTML = '<img class="img-preview" src="' + diagB64 + '">';
}
async function diagnosePhoto(){
  const btn = document.getElementById('photoBtn');
  const c = document.getElementById('photoResult');
  if (!diagB64){ toast('Select photo', 'warning'); return; }
  btn.disabled = true; btn.innerHTML = '📸 Analyzing...';
  c.innerHTML = skeleton();
  try {
    const d = await jpost('/api/diagnose/photo', {image_base64:diagB64, vehicle_info:document.getElementById('photoVehicle').value});
    if (!d.success){ c.innerHTML = ''; toast(d.error || 'Failed', 'error'); }
    else {
      let h = '<div class="card"><h3>🔍 ' + esc(d.problem || 'Detected') + '</h3>' +
        '<p><strong>Confidence:</strong> ' + (d.confidence || '?') + '</p>' +
        (d.description ? '<p style="margin-top:8px">' + esc(d.description) + '</p>' : '') + '</div>';
      if (d.possible_causes && d.possible_causes.length) h += '<div class="card"><h3>Causes</h3>' + d.possible_causes.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '</div>';
      if (d.diagnostic_steps && d.diagnostic_steps.length) h += '<div class="card"><h3>Steps</h3>' + d.diagnostic_steps.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '</div>';
      if (d.safety_warnings && d.safety_warnings.length) h += '<div class="card" style="background:#fef2f2"><h3 style="color:var(--danger)">⚠️ Safety</h3>' + d.safety_warnings.map(x => '<div class="list-item">⚠ ' + esc(x) + '</div>').join('') + '</div>';
      c.innerHTML = h; toast('Analysis complete', 'success');
    }
  } catch(e){ c.innerHTML = ''; toast('Error', 'error'); }
  btn.disabled = false; btn.innerHTML = '📸 Analyze Photo';
}

// ═══════════════════════════════════
// PAINT
// ═══════════════════════════════════
let paintB64 = '';
async function previewPaint(e){
  const f = e.target.files[0]; if (!f) return;
  paintB64 = await compressImage(f, 1200, 0.75);
  document.getElementById('paintPreview').innerHTML = '<img class="img-preview" src="' + paintB64 + '">';
}
async function matchPaint(){
  const btn = document.getElementById('paintBtn');
  const c = document.getElementById('paintResult');
  if (!paintB64){ toast('Select photo', 'warning'); return; }
  btn.disabled = true; btn.innerHTML = '🎨 Analyzing...';
  c.innerHTML = skeleton();
  try {
    const d = await jpost('/api/paint/match', {image_base64:paintB64, vehicle_info:document.getElementById('paintVehicle').value});
    if (!d.success){ c.innerHTML = ''; toast(d.error || 'Failed', 'error'); }
    else {
      const col = d.detected_colour || {};
      let h = '<div class="card"><div class="swatch" style="background:' + (col.hex_code || '#ccc') + '"></div>' +
        '<h3>' + esc(col.name || 'Unknown') + '</h3>' +
        '<p><strong>' + esc(col.finish || '') + '</strong>' + (col.colour_family ? ' • ' + esc(col.colour_family) : '') + '</p>' +
        '<p style="font-family:monospace;margin-top:6px">' + (col.hex_code || '') + '</p></div>';
      if (d.brand_codes && d.brand_codes.length){
        h += '<div class="card"><h3>Brand Codes</h3>';
        d.brand_codes.forEach(b => { h += '<div class="list-item"><strong>' + esc(b.brand) + ':</strong> ' + esc(b.code || '?') + '</div>'; });
        h += '</div>';
      }
      c.innerHTML = h; toast('Match found', 'success');
    }
  } catch(e){ c.innerHTML = ''; toast('Error', 'error'); }
  btn.disabled = false; btn.innerHTML = '🎨 Match Colour';
}

// ═══════════════════════════════════
// SPECS
// ═══════════════════════════════════
let specsData = [];
async function loadSpecs(){
  if (!specsData.length){ try{ specsData = (await jget('/api/specs')).specs; }catch(e){ return; } }
  filterSpecs();
}
function filterSpecs(){
  const q = (document.getElementById('specsSearch').value || '').toLowerCase();
  const f = specsData.filter(x => !q || x.v.toLowerCase().includes(q));
  document.getElementById('specsList').innerHTML = f.length ? f.map(s =>
    '<div class="card"><h3>🔧 ' + esc(s.v) + '</h3>' +
    '<div class="list-item"><strong>Engine Code:</strong> ' + esc(s.engine_code) + '</div>' +
    '<div class="list-item"><strong>Oil:</strong> ' + esc(s.oil) + '</div>' +
    '<div class="list-item"><strong>Coolant:</strong> ' + esc(s.coolant) + '</div>' +
    '<div class="list-item"><strong>Brake:</strong> ' + esc(s.brake) + '</div>' +
    '<div class="list-item"><strong>Trans:</strong> ' + esc(s.trans) + '</div>' +
    '<div class="list-item"><strong>Timing:</strong> ' + esc(s.timing) + '</div></div>'
  ).join('') : emptyState('🔧','No match','Try different search.');
}

// ═══════════════════════════════════
// INTERVALS
// ═══════════════════════════════════
let intData = [];
async function loadIntervals(){
  if (!intData.length){ try{ intData = (await jget('/api/intervals')).intervals; }catch(e){ return; } }
  document.getElementById('intervalList').innerHTML = intData.map(s =>
    '<div class="card"><h3>⏰ ' + esc(s.t) + '</h3>' +
    '<div class="list-item"><strong>Every:</strong> ' + s.km + ' km / ' + s.months + ' months</div>' +
    s.items.map(i => '<div class="list-item">• ' + esc(i) + '</div>').join('') + '</div>'
  ).join('');
}

// ═══════════════════════════════════
// BOOK TIME
// ═══════════════════════════════════
let bookData = [];
async function loadBookTime(){
  if (!bookData.length){ try{ bookData = (await jget('/api/book-times')).times; }catch(e){ return; } }
  document.getElementById('bookList').innerHTML = bookData.map(b =>
    '<div class="card"><h3>⏱️ ' + esc(b.job) + '</h3><div class="list-item">Standard time: <strong>' + b.hrs + ' hours</strong></div></div>'
  ).join('');
}

// ═══════════════════════════════════
// SUPPLIERS
// ═══════════════════════════════════
async function loadSuppliers(){
  const c = document.getElementById('supplierList'); c.innerHTML = skeleton();
  try {
    const d = await jget('/api/suppliers');
    c.innerHTML = d.suppliers.length ? d.suppliers.map(s =>
      '<div class="card"><h3>📞 ' + esc(s.name) + '</h3>' +
      (s.category ? '<p style="font-size:12px;color:var(--text2)">' + esc(s.category) + '</p>' : '') +
      (s.phone ? '<p>📞 ' + esc(s.phone) + '</p>' : '') +
      (s.email ? '<p>📧 ' + esc(s.email) + '</p>' : '') +
      '<div style="margin-top:10px">' +
      (s.phone ? '<button class="btn-sm blue" onclick="window.location.href=\'tel:' + esc(s.phone) + '\'">📞 Call</button>' : '') +
      (s.whatsapp ? '<button class="btn-sm wa" onclick="window.open(\'https://wa.me/' + esc(s.whatsapp).replace(/[^0-9]/g,'') + '\',\'_blank\')">📱</button>' : '') +
      '<button class="btn-sm red" onclick="delSupplier(\'' + s.id + '\')">Delete</button></div></div>'
    ).join('') : emptyState('📞','No suppliers','Add suppliers for fast ordering.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Failed to load.'); }
}
async function addSupplier(){
  const n = document.getElementById('supName').value.trim();
  if (!n){ toast('Name required', 'warning'); return; }
  await jpost('/api/suppliers', {name:n,phone:document.getElementById('supPhone').value,email:document.getElementById('supEmail').value,whatsapp:document.getElementById('supWhatsapp').value,category:document.getElementById('supCategory').value,account_number:document.getElementById('supAccount').value});
  ['supName','supPhone','supEmail','supWhatsapp','supCategory','supAccount'].forEach(id => document.getElementById(id).value = '');
  hideForm('supplierForm'); toast('Supplier added ✓', 'success'); loadSuppliers();
}
async function delSupplier(id){ if (!confirm('Delete?')) return; await fetch('/api/suppliers/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadSuppliers(); }

// ═══════════════════════════════════
// CODES
// ═══════════════════════════════════
async function searchCodes(){
  const q = document.getElementById('codeSearch').value;
  const c = document.getElementById('codeResults'); c.innerHTML = skeleton();
  try {
    const d = await jget('/api/fault-codes?search=' + encodeURIComponent(q));
    c.dataset.loaded = '1';
    c.innerHTML = d.codes.length ? d.codes.map(x =>
      '<div class="card"><h3>' + x.code + '<span class="badge ' + x.severity.toLowerCase() + '">' + x.severity + '</span></h3>' +
      '<p><strong>' + esc(x.description) + '</strong></p>' +
      '<p style="color:var(--text2);font-size:12px">' + esc(x.system) + '</p>' +
      '<p style="margin-top:8px"><strong>Causes:</strong></p>' + x.causes.map(y => '<div class="list-item">• ' + esc(y) + '</div>').join('') +
      '<p style="margin-top:8px"><strong>Steps:</strong></p>' + x.steps.map(y => '<div class="list-item">• ' + esc(y) + '</div>').join('') + '</div>'
    ).join('') : emptyState('📟','No match','Try a different code.');
  } catch(e){ c.innerHTML = ''; toast('Failed', 'error'); }
}

// ═══════════════════════════════════
// JOBS
// ═══════════════════════════════════
async function loadStaffDropdown(){
  try { const d = await jget('/api/staff'); const sel = document.getElementById('jAssigned'); if (sel) sel.innerHTML = '<option value="">— Assign —</option>' + d.staff.map(s => '<option value="' + esc(s.name) + '">' + esc(s.name) + '</option>').join(''); } catch(e){}
}
async function loadJobs(){
  const c = document.getElementById('jobList'); c.innerHTML = skeleton();
  try {
    const d = await jget('/api/jobs');
    c.innerHTML = d.jobs.length ? d.jobs.map(j =>
      '<div class="card"><h3>Job #' + j.id + ' <span class="badge ' + j.status.toLowerCase().replace(' ','') + '">' + j.status + '</span></h3>' +
      '<p><strong>' + esc(j.customer) + '</strong></p>' +
      '<p>🚗 ' + esc(j.vehicle) + (j.registration ? ' (' + esc(j.registration) + ')' : '') + '</p>' +
      '<p style="color:var(--text2)">' + esc(j.complaint) + '</p>' +
      '<div style="margin-top:10px">' +
      '<button class="btn-sm blue" onclick="upJob(\'' + j.id + '\',\'In Progress\')">Progress</button>' +
      '<button class="btn-sm green" onclick="upJob(\'' + j.id + '\',\'Completed\')">Done</button>' +
      '<button class="btn-sm wa" onclick="waJob(\'' + j.id + '\')">📱</button>' +
      '<button class="btn-sm red" onclick="delJob(\'' + j.id + '\')">Delete</button></div></div>'
    ).join('') : emptyState('📋','No jobs yet','Tap + New Job to create one.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Failed to load.'); }
}
async function createJob(){
  const c = document.getElementById('jCustomer').value.trim();
  const v = document.getElementById('jVehicle').value.trim();
  const comp = document.getElementById('jComplaint').value.trim();
  if (!c || !v || !comp){ toast('Fill required fields', 'warning'); return; }
  await jpost('/api/jobs', {customer:c,phone:document.getElementById('jPhone').value,vehicle:v,registration:document.getElementById('jReg').value,complaint:comp,assigned_to:document.getElementById('jAssigned').value,warranty_months:parseInt(document.getElementById('jWarranty').value) || 6});
  ['jCustomer','jPhone','jVehicle','jReg','jComplaint'].forEach(id => document.getElementById(id).value = '');
  hideForm('jobForm'); toast('Job created ✓', 'success'); loadJobs();
}
async function upJob(id, s){ await jput('/api/jobs/' + id, {status:s}); toast('Updated', 'success'); loadJobs(); }
async function delJob(id){ if (!confirm('Delete?')) return; await fetch('/api/jobs/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadJobs(); }
function waJob(id){ jget('/api/jobs').then(d => { const j = d.jobs.find(x => x.id == id); const txt = '🔧 Job #' + j.id + '\n' + j.customer + '\nStatus: ' + j.status; window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank'); }); }

// ═══════════════════════════════════
// QUOTES
// ═══════════════════════════════════
async function loadQuotes(){
  const c = document.getElementById('quoteList'); c.innerHTML = skeleton();
  try {
    const d = await jget('/api/quotes');
    c.innerHTML = d.quotes.length ? d.quotes.map(q =>
      '<div class="card"><h3>💬 Quote #' + q.id + '</h3>' +
      '<p><strong>' + esc(q.customer) + '</strong></p><p>' + esc(q.description) + '</p>' +
      '<div class="list-item"><strong>Total: R' + q.total.toFixed(2) + '</strong></div>' +
      '<div style="margin-top:10px">' +
      '<button class="btn-sm green" onclick="acceptQuote(\'' + q.id + '\')">→ Invoice</button>' +
      '<button class="btn-sm red" onclick="delQuote(\'' + q.id + '\')">Delete</button></div></div>'
    ).join('') : emptyState('💬','No quotes','Create one to send.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Failed.'); }
}
async function createQuote(){
  const c = document.getElementById('qCustomer').value.trim();
  const d = document.getElementById('qDesc').value.trim();
  if (!c || !d){ toast('Fill required', 'warning'); return; }
  await jpost('/api/quotes', {customer:c,vehicle:document.getElementById('qVehicle').value,description:d,labour:parseFloat(document.getElementById('qLabour').value) || 0,parts:parseFloat(document.getElementById('qParts').value) || 0});
  ['qCustomer','qVehicle','qDesc','qLabour','qParts'].forEach(id => document.getElementById(id).value = '');
  hideForm('quoteForm'); toast('Quote created ✓', 'success'); loadQuotes();
}
async function acceptQuote(id){ if (!confirm('Convert?')) return; const r = await jpost('/api/quotes/' + id + '/accept', {}); if (r.success){ toast('Converted ✓', 'success'); loadQuotes(); } }
async function delQuote(id){ if (!confirm('Delete?')) return; await fetch('/api/quotes/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadQuotes(); }

// ═══════════════════════════════════
// APPOINTMENTS
// ═══════════════════════════════════
async function loadAppts(){
  const c = document.getElementById('apptList'); c.innerHTML = skeleton();
  try {
    const d = await jget('/api/appointments');
    const s = d.appointments.sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time));
    c.innerHTML = s.length ? s.map(a =>
      '<div class="card"><h3>📅 ' + esc(a.date) + ' ' + esc(a.time) + '</h3>' +
      '<p><strong>' + esc(a.customer) + '</strong></p>' +
      (a.vehicle ? '<p>🚗 ' + esc(a.vehicle) + '</p>' : '') +
      '<button class="btn-sm red" onclick="delAppt(\'' + a.id + '\')">Delete</button></div>'
    ).join('') : emptyState('📅','No appointments','Book one.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Failed.'); }
}
async function createAppt(){
  const c = document.getElementById('aCustomer').value.trim();
  const d = document.getElementById('aDate').value;
  const t = document.getElementById('aTime').value;
  if (!c || !d || !t){ toast('Fill required', 'warning'); return; }
  await jpost('/api/appointments', {customer:c,phone:document.getElementById('aPhone').value,vehicle:document.getElementById('aVehicle').value,service:document.getElementById('aService').value,date:d,time:t});
  ['aCustomer','aPhone','aVehicle','aService','aDate','aTime'].forEach(id => document.getElementById(id).value = '');
  hideForm('apptForm'); toast('Booked ✓', 'success'); loadAppts();
}
async function delAppt(id){ if (!confirm('Delete?')) return; await fetch('/api/appointments/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadAppts(); }

// ═══════════════════════════════════
// CUSTOMERS
// ═══════════════════════════════════
async function loadCust(){
  const c = document.getElementById('custList'); c.innerHTML = skeleton();
  try {
    const d = await jget('/api/customers');
    c.innerHTML = d.customers.length ? d.customers.map(x =>
      '<div class="card"><h3>👤 ' + esc(x.name) + '</h3>' +
      '<p>📞 ' + esc(x.phone) + '</p>' +
      (x.email ? '<p>📧 ' + esc(x.email) + '</p>' : '') +
      '<div style="margin-top:10px">' +
      '<button class="btn-sm wa" onclick="waCust(\'' + esc(x.phone) + '\')">📱</button>' +
      '<button class="btn-sm red" onclick="delCust(\'' + x.id + '\')">Delete</button></div></div>'
    ).join('') : emptyState('👥','No customers','Add first customer.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Failed.'); }
}
async function createCustomer(){
  const n = document.getElementById('cName').value.trim();
  const p = document.getElementById('cPhone').value.trim();
  if (!n || !p){ toast('Name and phone required', 'warning'); return; }
  await jpost('/api/customers', {name:n,phone:p,email:document.getElementById('cEmail').value});
  ['cName','cPhone','cEmail'].forEach(id => document.getElementById(id).value = '');
  hideForm('custForm'); toast('Added ✓', 'success'); loadCust();
}
async function delCust(id){ if (!confirm('Delete?')) return; await fetch('/api/customers/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadCust(); }
function waCust(p){ window.open('https://wa.me/' + p.replace(/[^0-9]/g,''), '_blank'); }

// ═══════════════════════════════════
// INVOICES
// ═══════════════════════════════════
async function loadInv(){
  const c = document.getElementById('invList'); c.innerHTML = skeleton();
  try {
    const d = await jget('/api/invoices');
    c.innerHTML = d.invoices.length ? d.invoices.map(i =>
      '<div class="card"><h3>Inv #' + i.id + '</h3>' +
      '<p><strong>' + esc(i.customer) + '</strong></p>' +
      '<p>' + esc(i.description) + '</p>' +
      '<div class="list-item"><strong>Total: R' + i.total.toFixed(2) + '</strong></div>' +
      '<div style="margin-top:10px">' +
      '<button class="btn-sm wa" onclick="waInv(\'' + i.id + '\')">📱</button>' +
      '<button class="btn-sm red" onclick="delInv(\'' + i.id + '\')">Delete</button></div></div>'
    ).join('') : emptyState('💰','No invoices','Create one to bill.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Failed.'); }
}
async function createInvoice(){
  const c = document.getElementById('iCustomer').value.trim();
  const d = document.getElementById('iDesc').value.trim();
  if (!c || !d){ toast('Fill required', 'warning'); return; }
  await jpost('/api/invoices', {customer:c,vehicle:document.getElementById('iVehicle').value,description:d,labour:parseFloat(document.getElementById('iLabour').value) || 0,parts:parseFloat(document.getElementById('iParts').value) || 0});
  ['iCustomer','iVehicle','iDesc','iLabour','iParts'].forEach(id => document.getElementById(id).value = '');
  hideForm('invForm'); toast('Invoice created ✓', 'success'); loadInv();
}
async function delInv(id){ if (!confirm('Delete?')) return; await fetch('/api/invoices/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadInv(); }
function waInv(id){ jget('/api/invoices').then(d => { const i = d.invoices.find(x => x.id == id); const txt = '💰 Invoice #' + i.id + '\n' + i.customer + '\nTotal: R' + i.total.toFixed(2); window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank'); }); }

// ═══════════════════════════════════
// INVENTORY
// ═══════════════════════════════════
async function loadInventory(){
  const c = document.getElementById('inventoryList'); c.innerHTML = skeleton();
  try {
    const d = await jget('/api/inventory');
    c.innerHTML = d.items.length ? d.items.map(i => {
      const cls = i.qty <= i.min_qty ? 'warn' : 'ok';
      return '<div class="card"><h3>' + esc(i.name) + ' <span class="badge ' + cls + '">' + i.qty + '</span></h3>' +
        '<div class="list-item">Cost: R' + i.cost_price.toFixed(2) + ' | Sell: R' + i.sell_price.toFixed(2) + '</div>' +
        '<div style="margin-top:10px">' +
        '<button class="btn-sm green" onclick="adjInv(\'' + i.id + '\',1)">+1</button>' +
        '<button class="btn-sm red" onclick="adjInv(\'' + i.id + '\',-1)">-1</button>' +
        '<button class="btn-sm gray" onclick="delInvItem(\'' + i.id + '\')">Delete</button></div></div>';
    }).join('') : emptyState('📦','No stock','Add parts you keep.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Failed.'); }
}
async function addInventory(){
  const n = document.getElementById('pName').value.trim();
  if (!n){ toast('Name required', 'warning'); return; }
  await jpost('/api/inventory', {part_number:document.getElementById('pNumber').value,name:n,category:document.getElementById('pCategory').value,qty:parseInt(document.getElementById('pQty').value) || 0,min_qty:parseInt(document.getElementById('pMinQty').value) || 5,cost_price:parseFloat(document.getElementById('pCost').value) || 0,sell_price:parseFloat(document.getElementById('pSell').value) || 0,supplier:document.getElementById('pSupplier').value});
  ['pNumber','pName','pCategory','pQty','pMinQty','pCost','pSell','pSupplier'].forEach(id => document.getElementById(id).value = '');
  hideForm('invItemForm'); toast('Item added ✓', 'success'); loadInventory();
}
async function adjInv(id, d){ await jpost('/api/inventory/' + id + '/adjust', {delta:d}); loadInventory(); }
async function delInvItem(id){ if (!confirm('Delete?')) return; await fetch('/api/inventory/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadInventory(); }

// ═══════════════════════════════════
// STAFF
// ═══════════════════════════════════
async function loadStaff(){
  const c = document.getElementById('staffList'); c.innerHTML = skeleton();
  try {
    const d = await jget('/api/staff');
    c.innerHTML = d.staff.length ? d.staff.map(s =>
      '<div class="card"><h3>👷 ' + esc(s.name) + '</h3>' +
      (s.role ? '<p><strong>' + esc(s.role) + '</strong></p>' : '') +
      (s.phone ? '<p>📞 ' + esc(s.phone) + '</p>' : '') +
      '<p>Rate: R' + s.hourly_rate.toFixed(2) + '/hr</p>' +
      '<button class="btn-sm red" onclick="delStaff(\'' + s.id + '\')">Delete</button></div>'
    ).join('') : emptyState('👷','No staff','Add team members.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Failed.'); }
}
async function addStaff(){
  const n = document.getElementById('stName').value.trim();
  if (!n){ toast('Name required', 'warning'); return; }
  await jpost('/api/staff', {name:n,role:document.getElementById('stRole').value,phone:document.getElementById('stPhone').value,email:document.getElementById('stEmail').value,hourly_rate:parseFloat(document.getElementById('stRate').value) || 150});
  ['stName','stRole','stPhone','stEmail'].forEach(id => document.getElementById(id).value = '');
  hideForm('staffForm'); toast('Added ✓', 'success'); loadStaff();
}
async function delStaff(id){ if (!confirm('Delete?')) return; await fetch('/api/staff/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadStaff(); }

// ═══════════════════════════════════
// EXPENSES
// ═══════════════════════════════════
async function loadExpenses(){
  const c = document.getElementById('expenseList'); c.innerHTML = skeleton();
  try {
    const d = await jget('/api/expenses');
    const total = d.expenses.reduce((s, x) => s + parseFloat(x.amount || 0), 0);
    let h = '<div class="card" style="background:var(--grad-danger);color:white"><h3 style="color:white">Total</h3><p style="font-size:28px;color:white;font-weight:800">R' + total.toFixed(2) + '</p></div>';
    h += d.expenses.length ? d.expenses.map(e =>
      '<div class="card"><h3>' + esc(e.category) + ' <span class="badge new">R' + parseFloat(e.amount).toFixed(2) + '</span></h3>' +
      (e.note ? '<p>' + esc(e.note) + '</p>' : '') +
      '<button class="btn-sm red" onclick="delExpense(\'' + e.id + '\')">Delete</button></div>'
    ).join('') : emptyState('💸','No expenses','Track costs.');
    c.innerHTML = h;
  } catch(e){ c.innerHTML = emptyState('❌','Error','Failed.'); }
}
async function addExpense(){
  const a = parseFloat(document.getElementById('exAmount').value) || 0;
  if (!a){ toast('Amount required', 'warning'); return; }
  await jpost('/api/expenses', {category:document.getElementById('exCat').value,amount:a,date:document.getElementById('exDate').value || new Date().toISOString().slice(0,10),note:document.getElementById('exNote').value});
  ['exAmount','exDate','exNote'].forEach(id => document.getElementById(id).value = '');
  hideForm('expForm'); toast('Added ✓', 'success'); loadExpenses();
}
async function delExpense(id){ if (!confirm('Delete?')) return; await fetch('/api/expenses/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadExpenses(); }

// ═══════════════════════════════════
// TORQUE
// ═══════════════════════════════════
let torqueData = [], seqData = [];
async function loadTorque(){
  if (!torqueData.length){ try{ const d = await jget('/api/torque'); torqueData = d.bolts; seqData = d.sequences; }catch(e){ return; } }
  filterTorque();
}
function filterTorque(){
  const q = (document.getElementById('torqueSearch').value || '').toLowerCase();
  const f = torqueData.filter(x => !q || x.s.toLowerCase().includes(q) || x.g.toLowerCase().includes(q));
  document.getElementById('torqueTable').innerHTML = '<table class="torque-table"><tr><th>Size</th><th>Grade</th><th>Nm</th><th>ft·lb</th><th>Use</th></tr>' +
    f.map(x => '<tr><td><strong>' + esc(x.s) + '</strong></td><td>' + esc(x.g) + '</td><td>' + x.nm + '</td><td>' + x.ft + '</td><td>' + esc(x.u) + '</td></tr>').join('') + '</table>';
  document.getElementById('torqueSeq').innerHTML = seqData.map(s => '<div class="card"><h3>' + esc(s.c) + '</h3>' + s.st.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '</div>').join('');
}

async function calcTorque(){
  const d = await jpost('/api/bolt-calc', {size:document.getElementById('boltSize').value,grade:document.getElementById('boltGrade').value,condition:document.getElementById('boltCondition').value});
  document.getElementById('boltResult').innerHTML = '<div class="card" style="background:var(--grad1);color:white"><h3 style="color:white">Torque</h3><p style="font-size:34px;font-weight:800;color:white;margin:8px 0">' + d.nm.toFixed(1) + ' Nm</p><p style="color:whi
te">' + d.ftlb.toFixed(1) + ' ft·lb</p></div>';
}

// BULBS/BATT/TYRES/WIRING/OBD
let bulbsData = [], battData = [], tyreData = [], wiringData = [], obdData = [];
async function loadBulbs(){ if (!bulbsData.length){ try{ bulbsData = (await jget('/api/bulbs')).bulbs; }catch(e){} } document.getElementById('bulbList').innerHTML = bulbsData.map(b => '<div class="card"><h3>💡 ' + esc(b.v) + '</h3><div class="list-item">Low: <strong>' + esc(b.l) + '</strong></div><div class="list-item
