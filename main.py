from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from datetime import datetime, timedelta
import openai, os, uuid, csv, io, json

app = FastAPI()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

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
        DB_READY = True; print("[db] Supabase connected")
    except Exception as e: print(f"[db] Failed: {e}")

init_db()

MEM = {"jobs":{}, "customers":{}, "invoices":{}, "quotes":{}, "appointments":{},
       "inventory":{}, "staff":{}, "expenses":{}, "suppliers":{}}
WORKSHOP = {"name":"My Workshop","phone":"","address":"","logo":"🔧","labour_rate":450,
            "vat_number":"","company_reg":"","bank_details":"","email":"","hours":"",
            "terms":"Payment due within 30 days. Parts warranty per manufacturer. Labour warranty 6 months."}

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
    MEM[t][i] = row; return row

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
    {"s":"M20","g":"8.8","nm":425,"ft":313,"u":"Truck chassis"},{"s":"M8","g":"10.9","nm":35,"ft":25.8,"u":"Head (small)"},
    {"s":"M10","g":"10.9","nm":70,"ft":51.6,"u":"Head bolts"},{"s":"M12","g":"10.9","nm":120,"ft":88.5,"u":"Head/main bolts"},
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
    {"n":"Charging System","sy":"Charging","d":"Alternator, battery, warning light",
     "c":["Battery 12V","Alternator","Ignition switch","Warning light"],
     "co":["Battery + → Alt B+ (Red, 6mm²)","Battery - → Ground","Alt D+ → Warning light","Warning light → IGN 15"],
     "nt":["Output: 13.8-14.4V","Warning light ON with engine off is normal"]},
    {"n":"Starting System","sy":"Starting","d":"Starter, relay, ignition",
     "c":["Battery","Ignition switch","Starter relay","Starter motor"],
     "co":["Battery + → Starter 30 (25mm²)","IGN 50 → Relay 86","Relay 87 → Starter 50","Relay 85 → Ground"],
     "nt":["Don't hold starter over 10 sec"]},
    {"n":"Engine Sensors","sy":"Engine","d":"MAF, MAP, TPS, ECT, O2 to ECU",
     "c":["ECU","MAF","MAP","TPS","ECT","O2"],
     "co":["ECU → MAF: signal+ground+power+IAT","ECU → MAP: signal+ground+5V","ECU → TPS: 5V+signal+ground"],
     "nt":["Reference: 4.9-5.1V","MAF: 0.5-4.5V output"]},
    {"n":"Headlight Circuit","sy":"Lighting","d":"Relay-controlled headlights",
     "c":["Battery","Headlight switch","Low relay","High relay","Headlights"],
     "co":["Battery + → Relay 30","Switch 56 → Low relay 86","Relay 87 → Headlight +"],
     "nt":["Voltage drop < 0.5V"]},
    {"n":"ABS Wheel Sensors","sy":"ABS","d":"4-channel wheel speed",
     "c":["ABS ECU","FL/FR/RL/RR sensors","Pump motor"],
     "co":["ABS → FL (White+Black)","ABS → FR (Yellow+Green)","ABS → RL (Blue+Grey)","ABS → RR (Brown+Purple)"],
     "nt":["Resistance: 800-1400Ω","Air gap: 0.5-1.5mm"]},
    {"n":"Diesel Glow Plugs","sy":"Diesel","d":"Glow relay circuit",
     "c":["Battery","Ignition","Glow relay","Glow plugs 1-4"],
     "co":["Battery + → Relay 30","IGN 15 → Relay 86","Relay 87 → All glow plugs"],
     "nt":["Resistance: 0.5-2Ω"]},
    {"n":"Transmission Control","sy":"Transmission","d":"TCM, solenoids, sensors",
     "c":["TCM","Shift sol A/B/C","Line pressure solenoid","ISS/OSS"],
     "co":["TCM → Sol A (Red)","TCM → Sol B (Blue)","TCM → Line pressure (Yellow)","TCM → ISS (White)","TCM → OSS (Brown)"],
     "nt":["Solenoid: 10-15Ω"]},
    {"n":"Petrol Fuel Injection","sy":"Fuel","d":"Injectors and pump",
     "c":["ECU","Injectors 1-4","Fuel relay","Fuel pump"],
     "co":["ECU → Injector drivers","ECU → Common 12V","ECU → Relay 86","Relay 87 → Fuel pump"],
     "nt":["Injector: 12-16Ω"]},
    {"n":"CAN Bus Network","sy":"Network","d":"Multi-module communication",
     "c":["ECM","TCM","BCM","ABS","DLC"],
     "co":["All: CAN-H (Yellow) twisted","All: CAN-L (Green) twisted","DLC pin 6=H, pin 14=L"],
     "nt":["Termination: 60Ω"]},
    {"n":"Immobilizer","sy":"Security","d":"Key transponder circuit",
     "c":["IMMO ECU","Antenna","Status LED","ECM"],
     "co":["IMMO → Antenna","IMMO → ECM (CAN)","IMMO → LED"],
     "nt":["Antenna: 5-20Ω"]},
]
PIDS = [
    {"p":"0100","n":"PIDs supported","d":"Bit-encoded supported PIDs"},
    {"p":"0101","n":"Monitor status","d":"MIL + readiness monitors"},
    {"p":"0103","n":"Fuel system status","d":"Open/closed loop"},
    {"p":"0104","n":"Calculated engine load","d":"% of max"},
    {"p":"0105","n":"Engine coolant temp","d":"°C"},
    {"p":"0106","n":"Short fuel trim B1","d":"%"},
    {"p":"0107","n":"Long fuel trim B1","d":"%"},
    {"p":"010B","n":"Intake manifold pressure","d":"kPa"},
    {"p":"010C","n":"Engine RPM","d":"((A*256)+B)/4"},
    {"p":"010D","n":"Vehicle speed","d":"km/h"},
    {"p":"010E","n":"Timing advance","d":"° BTDC"},
    {"p":"010F","n":"Intake air temp","d":"°C"},
    {"p":"0110","n":"MAF flow rate","d":"g/s"},
    {"p":"0111","n":"Throttle position","d":"%"},
    {"p":"011F","n":"Run time since start","d":"seconds"},
    {"p":"012F","n":"Fuel level","d":"%"},
    {"p":"0133","n":"Barometric pressure","d":"kPa"},
    {"p":"0142","n":"Control module voltage","d":"V"},
    {"p":"0146","n":"Ambient air temp","d":"°C"},
    {"p":"015C","n":"Engine oil temp","d":"°C"},
]

# ═══ VEHICLE SPECS DATABASE ═══
VEHICLE_SPECS = [
    {"v":"Toyota Hilux 2.8 GD-6 (2016+)","oil":"7.5L 5W-30","coolant":"8.2L Toyota SLLC","brake":"DOT 4","trans":"ATF WS 3.5L","engine_code":"1GD-FTV","firing":"1-3-4-2","timing":"Chain"},
    {"v":"Toyota Hilux 2.4 GD-6","oil":"7.5L 5W-30","coolant":"8.0L Toyota SLLC","brake":"DOT 4","trans":"ATF WS 3.5L","engine_code":"2GD-FTV","firing":"1-3-4-2","timing":"Chain"},
    {"v":"Toyota Hilux 2.5 D-4D","oil":"6.9L 10W-40","coolant":"7.4L Toyota LLC","brake":"DOT 4","trans":"75W-90 GL-4","engine_code":"2KD-FTV","firing":"1-3-4-2","timing":"Belt @150k"},
    {"v":"Ford Ranger 2.2 TDCi","oil":"6.8L 5W-30","coolant":"9.0L Motorcraft","brake":"DOT 4","trans":"ATF Mercon LV","engine_code":"P4AT","firing":"1-3-4-2","timing":"Belt @150k"},
    {"v":"Ford Ranger 3.2 TDCi","oil":"8.9L 5W-30","coolant":"10.5L Motorcraft","brake":"DOT 4","trans":"ATF Mercon LV","engine_code":"P5AT","firing":"1-2-3-4-5","timing":"Chain"},
    {"v":"VW Polo 1.4","oil":"3.8L 5W-30","coolant":"5.5L G13","brake":"DOT 4","trans":"75W-90","engine_code":"CLPA","firing":"1-3-4-2","timing":"Chain"},
    {"v":"VW Golf 1.4 TSI","oil":"4.0L 5W-30","coolant":"7.0L G13","brake":"DOT 4","trans":"ATF DSG 1.7L","engine_code":"CXSA","firing":"1-3-4-2","timing":"Chain"},
    {"v":"BMW 320i (F30)","oil":"5.0L 0W-40","coolant":"7.0L BMW Blue","brake":"DOT 4","trans":"ATF ZF 8HP","engine_code":"N20B20","firing":"1-3-4-2","timing":"Chain"},
    {"v":"Mercedes C200 (W205)","oil":"6.5L 5W-40","coolant":"7.5L MB 325.0","brake":"DOT 4 Plus","trans":"ATF 7G-Tronic","engine_code":"M274","firing":"1-3-4-2","timing":"Chain"},
    {"v":"Isuzu D-Max 2.5","oil":"6.5L 15W-40","coolant":"7.8L Isuzu Blue","brake":"DOT 4","trans":"ATF Dexron III","engine_code":"4JK1-TC","firing":"1-3-4-2","timing":"Chain"},
    {"v":"Nissan NP200 1.6","oil":"4.3L 5W-40","coolant":"6.5L Nissan LLC","brake":"DOT 4","trans":"75W-80","engine_code":"K4M","firing":"1-3-4-2","timing":"Belt @100k"},
    {"v":"Hyundai i20 1.4","oil":"3.6L 5W-30","coolant":"5.3L Hyundai LLC","brake":"DOT 4","trans":"75W-85","engine_code":"G4FA","firing":"1-3-4-2","timing":"Chain"},
]

# ═══ SERVICE INTERVALS ═══
INTERVALS = [
    {"t":"Petrol Vehicle","km":15000,"months":12,"items":["Oil + oil filter","Air filter check","Spark plugs check","Brake inspection","Tyre rotation","Fluids top-up","Battery test"]},
    {"t":"Diesel Vehicle","km":10000,"months":6,"items":["Oil + oil filter","Fuel filter","Air filter","Water separator drain","Brake inspection","Glow plug check"]},
    {"t":"Truck / Heavy Diesel","km":25000,"months":6,"items":["Oil + oil filter","Fuel filter","Air dryer","Brake check","Air filter","Coolant check","Grease points"]},
    {"t":"Motorcycle","km":6000,"months":6,"items":["Oil + filter","Chain lube + adjust","Brake check","Tyre pressure","Air filter clean","Spark plug check"]},
    {"t":"Tractor / Plant","km":500,"months":3,"items":["Oil + filter (engine hours)","Hydraulic filter","Fuel filter","Air filter","Grease all points","Coolant check"]},
]

# ═══ BOOK TIME / LABOUR GUIDE ═══
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
    {"job":"Suspension — Shock Absorber (each)","hrs":1.5},
    {"job":"Wheel Alignment","hrs":1.0},
    {"job":"Battery Replace","hrs":0.3},
    {"job":"Diagnostic Scan","hrs":0.5},
    {"job":"Full Service (Petrol)","hrs":2.0},
    {"job":"Full Service (Diesel)","hrs":2.5},
]

HTML = r"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RamsTech</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#f0f2f5;--card:#fff;--text:#1a1a2e;--text2:#6b7280;--border:#e5e7eb;--primary:#E65100}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:var(--bg);color:var(--text);padding-bottom:80px}
.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:16px;text-align:center;border-bottom-left-radius:24px;border-bottom-right-radius:24px;box-shadow:0 6px 24px rgba(102,126,234,.35)}
.header h1{font-size:20px;font-weight:800}
.header p{font-size:11px;opacity:.9;margin-top:3px}
.panel{display:none;padding:16px;max-width:800px;margin:0 auto;padding-bottom:100px}
.panel.active{display:block}
.panel-title{font-size:20px;font-weight:800;color:var(--primary);margin-bottom:16px}
.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{background:var(--card);border-radius:16px;padding:20px 12px;cursor:pointer;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border)}
.tile:active{transform:scale(.95)}
.tile-icon{font-size:36px;margin-bottom:8px;display:block}
.tile-label{font-size:12px;font-weight:700}
.card{background:var(--card);padding:16px;border-radius:16px;margin-bottom:12px;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border)}
.card h3{color:var(--primary);margin-bottom:8px;font-size:15px;font-weight:700}
.card p{margin:4px 0;font-size:13px;line-height:1.5}
.form-input{width:100%;padding:14px;border:1.5px solid var(--border);border-radius:12px;font-size:15px;margin-bottom:10px;background:#f9fafb;font-family:inherit}
.form-input:focus{outline:none;border-color:var(--primary)}
.btn{width:100%;padding:15px;border:none;border-radius:12px;font-size:15px;font-weight:800;cursor:pointer;margin-bottom:10px;background:linear-gradient(135deg,#667eea,#764ba2);color:white}
.btn:active{transform:scale(.97)}
.btn-green{background:linear-gradient(135deg,#43e97b,#38f9d7)}
.btn-dark{background:linear-gradient(135deg,#4b5563,#1f2937)}
.btn-sm{padding:8px 12px;border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;margin-right:5px;margin-bottom:4px;background:var(--primary);color:white}
.btn-sm.green{background:#10b981}.btn-sm.red{background:#ef4444}.btn-sm.blue{background:#3b82f6}.btn-sm.gray{background:#6b7280}.btn-sm.wa{background:#25D366}.btn-sm.purple{background:#8b5cf6}
.badge{display:inline-block;padding:3px 9px;border-radius:6px;font-size:11px;font-weight:700;color:white;margin-left:6px}
.badge.high{background:#ef4444}.badge.medium{background:#f59e0b}.badge.low,.badge.ok{background:#10b981}.badge.warn{background:#ef4444}
.badge.new{background:#6b7280}.badge.inprogress{background:#f59e0b}.badge.completed{background:#10b981}
.list-item{padding:8px 0;border-bottom:1px solid var(--border);font-size:13px}
.list-item:last-child{border-bottom:none}
.chat-box{background:var(--card);border-radius:16px;padding:14px;height:calc(100vh - 300px);overflow-y:auto;margin-bottom:12px;border:1px solid var(--border)}
.msg{padding:12px 16px;margin:8px 0;border-radius:16px;max-width:85%;word-wrap:break-word;font-size:14px;line-height:1.45}
.msg.user{background:linear-gradient(135deg,#667eea,#764ba2);color:white;margin-left:auto}
.msg.ai{background:#f9fafb;border:1px solid var(--border)}
.input-row{display:flex;gap:8px}
.input-row input{flex:1;padding:14px 18px;border:1.5px solid var(--border);border-radius:25px;font-size:15px;outline:none}
.input-row button{padding:14px 16px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:50%;font-weight:bold;font-size:16px}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--border);display:flex;padding:8px 4px;z-index:100}
.bnav{flex:1;text-align:center;padding:6px 4px;cursor:pointer;border-radius:12px}
.bnav.active{background:rgba(230,81,0,.08)}
.bnav-icon{font-size:20px;display:block;margin-bottom:2px}
.bnav-label{font-size:9px;font-weight:700;color:var(--text2);text-transform:uppercase}
.bnav.active .bnav-label{color:var(--primary)}
.loading{text-align:center;padding:20px;color:var(--text2);font-size:13px}
.status-online{background:linear-gradient(135deg,#10b981,#34d399);color:white;padding:10px 14px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700}
.status-offline{background:linear-gradient(135deg,#ef4444,#f87171);color:white;padding:10px 14px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700}
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat-card{background:var(--card);padding:16px 12px;border-radius:16px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border)}
.stat-card .num{font-size:22px;font-weight:800;color:var(--primary)}
.stat-card .lbl{font-size:10px;color:var(--text2);margin-top:4px;font-weight:600;text-transform:uppercase}
.stat-card.green .num{color:#10b981}.stat-card.red .num{color:#ef4444}.stat-card.blue .num{color:#3b82f6}.stat-card.purple .num{color:#8b5cf6}
canvas{max-height:220px}
.img-preview{width:100%;border-radius:14px;margin-bottom:12px}
.swatch{height:90px;border-radius:14px;border:2px solid var(--border);margin-bottom:12px}
.torque-table{width:100%;border-collapse:collapse;background:var(--card);border-radius:12px;overflow:hidden;font-size:12px;margin-bottom:12px}
.torque-table th{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:10px 8px;text-align:left;font-weight:700;font-size:11px}
.torque-table td{padding:10px 8px;border-bottom:1px solid var(--border);color:var(--text)}
.photo-row{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;margin-bottom:10px}
.photo-thumb{width:90px;height:90px;object-fit:cover;border-radius:10px;border:2px solid var(--border)}
.checklist-item{padding:10px 0;border-bottom:1px solid var(--border);font-size:13px;display:flex;align-items:center;gap:10px}
.checklist-item input{width:20px;height:20px;accent-color:var(--primary)}
</style>
</head><body>

<div class="header">
<h1>🔧 <span id="wsName">RAMSTECH</span></h1>
<p id="wsSub">AI Workshop Assistant</p>
</div>

<div id="home" class="panel active">
<div class="card"><div id="status">Checking...</div></div>
<div class="tile-grid">
<div class="tile" onclick="showTab('dashboard',this)"><span class="tile-icon">📊</span><div class="tile-label">Dashboard</div></div>
<div class="tile" onclick="showTab('chat',this)"><span class="tile-icon">🤖</span><div class="tile-label">AI Chat</div></div>
<div class="tile" onclick="showTab('codes',this)"><span class="tile-icon">📟</span><div class="tile-label">Fault Codes</div></div>
<div class="tile" onclick="showTab('vin',this)"><span class="tile-icon">🔍</span><div class="tile-label">VIN</div></div>
<div class="tile" onclick="showTab('photo',this)"><span class="tile-icon">📸</span><div class="tile-label">Photo Diag</div></div>
<div class="tile" onclick="showTab('paint',this)"><span class="tile-icon">🎨</span><div class="tile-label">Paint</div></div>
<div class="tile" onclick="showTab('specs',this)"><span class="tile-icon">🔧</span><div class="tile-label">Vehicle Specs</div></div>
<div class="tile" onclick="showTab('intervals',this)"><span class="tile-icon">⏰</span><div class="tile-label">Intervals</div></div>
<div class="tile" onclick="showTab('booktime',this)"><span class="tile-icon">⏱️</span><div class="tile-label">Book Time</div></div>
<div class="tile" onclick="showTab('suppliers',this)"><span class="tile-icon">📞</span><div class="tile-label">Suppliers</div></div>
<div class="tile" onclick="showTab('jobs',this)"><span class="tile-icon">📋</span><div class="tile-label">Jobs</div></div>
<div class="tile" onclick="showTab('quotes',this)"><span class="tile-icon">💬</span><div class="tile-label">Quotes</div></div>
<div class="tile" onclick="showTab('appointments',this)"><span class="tile-icon">📅</span><div class="tile-label">Appts</div></div>
<div class="tile" onclick="showTab('customers',this)"><span class="tile-icon">👥</span><div class="tile-label">Customers</div></div>
<div class="tile" onclick="showTab('invoices',this)"><span class="tile-icon">💰</span><div class="tile-label">Invoices</div></div>
<div class="tile" onclick="showTab('inventory',this)"><span class="tile-icon">📦</span><div class="tile-label">Inventory</div></div>
<div class="tile" onclick="showTab('staff',this)"><span class="tile-icon">👷</span><div class="tile-label">Staff</div></div>
<div class="tile" onclick="showTab('expenses',this)"><span class="tile-icon">💸</span><div class="tile-label">Expenses</div></div>
<div class="tile" onclick="showTab('analytics',this)"><span class="tile-icon">📈</span><div class="tile-label">Analytics</div></div>
<div class="tile" onclick="showTab('warranty',this)"><span class="tile-icon">🎁</span><div class="tile-label">Warranty</div></div>
<div class="tile" onclick="showTab('tax',this)"><span class="tile-icon">🧾</span><div class="tile-label">Tax</div></div>
<div class="tile" onclick="showTab('torque',this)"><span class="tile-icon">⚙️</span><div class="tile-label">Torque</div></div>
<div class="tile" onclick="showTab('boltcalc',this)"><span class="tile-icon">🔧</span><div class="tile-label">Bolt Calc</div></div>
<div class="tile" onclick="showTab('bulbs',this)"><span class="tile-icon">💡</span><div class="tile-label">Bulbs</div></div>
<div class="tile" onclick="showTab('batteries',this)"><span class="tile-icon">🔋</span><div class="tile-label">Batteries</div></div>
<div class="tile" onclick="showTab('tyres',this)"><span class="tile-icon">🛞</span><div class="tile-label">Tyres</div></div>
<div class="tile" onclick="showTab('wiring',this)"><span class="tile-icon">🔌</span><div class="tile-label">Wiring</div></div>
<div class="tile" onclick="showTab('obd',this)"><span class="tile-icon">⚡</span><div class="tile-label">OBD-II</div></div>
<div class="tile" onclick="showTab('settings',this)"><span class="tile-icon">⚙️</span><div class="tile-label">Settings</div></div>
</div>
</div>

<!-- SPECS -->
<div id="specs" class="panel">
<div class="panel-title">🔧 Vehicle Specifications</div>
<input type="text" class="form-input" id="specsSearch" placeholder="🔍 Search vehicle..." oninput="filterSpecs()">
<div id="specsList"><div class="loading">Loading...</div></div>
</div>

<!-- INTERVALS -->
<div id="intervals" class="panel">
<div class="panel-title">⏰ Service Intervals</div>
<input type="text" class="form-input" id="intervalSearch" placeholder="🔍 Search..." oninput="filterIntervals()">
<div id="intervalList"><div class="loading">Loading...</div></div>
</div>

<!-- BOOK TIME -->
<div id="booktime" class="panel">
<div class="panel-title">⏱️ Book Time / Labour Guide</div>
<input type="text" class="form-input" id="bookSearch" placeholder="🔍 Search job..." oninput="filterBook()">
<div id="bookList"><div class="loading">Loading...</div></div>
</div>

<!-- SUPPLIERS -->
<div id="suppliers" class="panel">
<div class="panel-title">📞 Suppliers</div>
<button class="btn btn-green" onclick="showForm('supplierForm')">+ Add Supplier</button>
<div id="supplierForm" style="display:none">
<div class="card">
<input class="form-input" id="supName" placeholder="Supplier name">
<input class="form-input" id="supPhone" placeholder="Phone">
<input class="form-input" id="supEmail" placeholder="Email">
<input class="form-input" id="supWhatsapp" placeholder="WhatsApp number">
<input class="form-input" id="supCategory" placeholder="Category (parts, electrical, body)">
<input class="form-input" id="supAccount" placeholder="Account number">
<textarea class="form-input" id="supNotes" placeholder="Notes" rows="2"></textarea>
<button class="btn btn-green" onclick="addSupplier()">Save Supplier</button>
<button class="btn btn-dark" onclick="hideForm('supplierForm')">Cancel</button>
</div>
</div>
<div id="supplierList"><div class="loading">Loading...</div></div>
</div>

<div id="dashboard" class="panel">
<div class="panel-title">📊 Dashboard</div>
<div id="dashStats"><div class="loading">Loading...</div></div>
<div class="card"><h3>💰 Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>📋 Job Status</h3><canvas id="jobChart"></canvas></div>
<div class="card"><h3>⚠️ Low Stock Alerts</h3><div id="dashLowStock"></div></div>
</div>

<div id="analytics" class="panel">
<div class="panel-title">📈 Analytics</div>
<div id="analyticsContent"><div class="loading">Loading...</div></div>
</div>

<div id="warranty" class="panel">
<div class="panel-title">🎁 Warranty Tracker</div>
<div id="warrantyList"><div class="loading">Loading...</div></div>
</div>

<div id="tax" class="panel">
<div class="panel-title">🧾 Tax & Reports</div>
<div class="card">
<h3>📅 Tax Report Period</h3>
<input class="form-input" id="taxFrom" type="date">
<input class="form-input" id="taxTo" type="date">
<button class="btn btn-dark" onclick="downloadTax()">📥 Download CSV</button>
</div>
</div>

<div id="vin" class="panel">
<div class="panel-title">🔍 VIN Decoder</div>
<div class="card">
<input class="form-input" id="vinInput" placeholder="17-character VIN" maxlength="17" style="text-transform:uppercase">
<button class="btn btn-green" onclick="decodeVin()">🔍 Decode</button>
<div id="vinResult"></div>
</div>
</div>

<div id="photo" class="panel">
<div class="panel-title">📸 Photo Diagnosis</div>
<div class="card">
<input class="form-input" id="photoVehicle" placeholder="Vehicle info">
<input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)">
<div id="photoPreview"></div>
<button class="btn btn-green" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze</button>
<div id="photoResult"></div>
</div>
</div>

<div id="paint" class="panel">
<div class="panel-title">🎨 Paint Match</div>
<div class="card">
<input class="form-input" id="paintVehicle" placeholder="Vehicle info">
<input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)">
<div id="paintPreview"></div>
<button class="btn btn-green" id="paintBtn" onclick="matchPaint()">🎨 Match Colour</button>
<div id="paintResult"></div>
</div>
</div>

<div id="torque" class="panel">
<div class="panel-title">⚙️ Torque Specs</div>
<input type="text" class="form-input" id="torqueSearch" placeholder="🔍 Search..." oninput="filterTorque()">
<h3 style="margin-bottom:8px;font-size:14px;color:var(--text2)">Bolt Torque</h3>
<div id="torqueTable"></div>
<h3 style="margin:16px 0 8px;font-size:14px;color:var(--text2)">Sequences</h3>
<div id="torqueSeq"></div>
</div>

<div id="boltcalc" class="panel">
<div class="panel-title">🔧 Bolt Calculator</div>
<div class="card">
<select class="form-input" id="boltSize"><option>M6</option><option>M8</option><option selected>M10</option><option>M12</option><option>M14</option><option>M16</option><option>M20</option></select>
<select class="form-input" id="boltGrade"><option>8.8</option><option selected>10.9</option><option>12.9</option></select>
<select class="form-input" id="boltCondition"><option value="dry">Dry</option><option value="oiled">Lightly oiled</option><option value="moly">Moly</option></select>
<button class="btn" onclick="calcTorque()">Calculate</button>
<div id="boltResult"></div>
</div>
</div>

<div id="bulbs" class="panel"><div class="panel-title">💡 Bulb Chart</div><input type="text" class="form-input" id="bulbSearch" placeholder="🔍 Search..." oninput="filterBulbs()"><div id="bulbList"><div class="loading">Loading...</div></div></div>
<div id="batteries" class="panel"><div class="panel-title">🔋 Batteries</div><input type="text" class="form-input" id="battSearch" placeholder="🔍 Search..." oninput="filterBatt()"><div id="battList"><div class="loading">Loading...</div></div></div>
<div id="tyres" class="panel"><div class="panel-title">🛞 Tyres</div><input type="text" class="form-input" id="tyreSearch" placeholder="🔍 Search..." oninput="filterTyre()"><div id="tyreList"><div class="loading">Loading...</div></div></div>
<div id="wiring" class="panel"><div class="panel-title">🔌 Wiring</div><input type="text" class="form-input" id="wiringSearch" placeholder="🔍 Search..." oninput="filterWiring()"><div id="wiringList"><div class="loading">Loading...</div></div></div>
<div id="obd" class="panel"><div class="panel-title">⚡ OBD-II PIDs</div><input type="text" class="form-input" id="obdSearch" placeholder="🔍 Search..." oninput="filterOBD()"><div id="obdList"><div class="loading">Loading...</div></div></div>

<div id="chat" class="panel">
<div class="panel-title">🤖 AI Assistant</div>
<div class="chat-box" id="chatBox"><div class="msg ai">Hi! Ask me about vehicle repairs.</div></div>
<div class="input-row">
<input type="text" id="chatInput" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendMsg()">
<button onclick="sendMsg()">➤</button>
</div>
</div>

<div id="codes" class="panel">
<div class="panel-title">📟 Fault Codes</div>
<input type="text" class="form-input" id="codeSearch" placeholder="🔍 Search code..." oninput="searchCodes()">
<div id="codeResults"><div class="loading">Loading...</div></div>
</div>

<div id="jobs" class="panel">
<div class="panel-title">📋 Job Cards</div>
<button class="btn btn-green" onclick="showForm('jobForm')">+ New Job</button>
<div id="jobForm" style="display:none">
<div class="card">
<input class="form-input" id="jCustomer" placeholder="Customer name">
<input class="form-input" id="jPhone" placeholder="Phone">
<input class="form-input" id="jVehicle" placeholder="Vehicle">
<input class="form-input" id="jReg" placeholder="Registration">
<textarea class="form-input" id="jComplaint" placeholder="Complaint" rows="2"></textarea>
<select class="form-input" id="jAssigned"><option value="">— Assign staff —</option></select>
<input class="form-input" id="jWarranty" type="number" placeholder="Warranty (months)" value="6">
<label style="font-size:13px;font-weight:700;display:block;margin-bottom:6px">📸 Before Photos</label>
<input type="file" id="jBefore" accept="image/*" multiple capture="environment" class="form-input" onchange="addPhoto(event,'before')">
<div class="photo-row" id="beforeRow"></div>
<button class="btn btn-green" onclick="createJob()">Save Job</button>
<button class="btn btn-dark" onclick="hideForm('jobForm')">Cancel</button>
</div>
</div>
<div id="jobList"><div class="loading">Loading...</div></div>
</div>

<div id="quotes" class="panel">
<div class="panel-title">💬 Quotes</div>
<button class="btn btn-green" onclick="showForm('quoteForm')">+ New Quote</button>
<div id="quoteForm" style="display:none">
<div class="card">
<input class="form-input" id="qCustomer" placeholder="Customer name">
<input class="form-input" id="qVehicle" placeholder="Vehicle">
<textarea class="form-input" id="qDesc" placeholder="Work description" rows="2"></textarea>
<label style="font-size:12px;font-weight:700">Book time (auto-fills labour)</label>
<select class="form-input" id="qBookTime" onchange="applyBookTime()">
<option value="">— Pick job —</option>
</select>
<input class="form-input" id="qLabour" type="number" placeholder="Labour (R)" value="0">
<input class="form-input" id="qParts" type="number" placeholder="Parts (R)" value="0">
<button class="btn btn-green" onclick="createQuote()">Save Quote</button>
<button class="btn btn-dark" onclick="hideForm('quoteForm')">Cancel</button>
</div>
</div>
<div id="quoteList"><div class="loading">Loading...</div></div>
</div>

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
<div id="apptList"><div class="loading">Loading...</div></div>
</div>

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
<div id="custList"><div class="loading">Loading...</div></div>
</div>

<div id="invoices" class="panel">
<div class="panel-title">💰 Invoices</div>
<button class="btn btn-green" onclick="showForm('invForm')">+ New Invoice</button>
<div id="invForm" style="display:none">
<div class="card">
<input class="form-input" id="iCustomer" placeholder="Customer">
<input class="form-input" id="iVehicle" placeholder="Vehicle">
<input class="form-input" id="iDesc" placeholder="Description">
<select class="form-input" id="iBookTime" onchange="applyInvBookTime()">
<option value="">— Pick job (auto labour) —</option>
</select>
<input class="form-input" id="iLabour" type="number" placeholder="Labour (R)">
<input class="form-input" id="iParts" type="number" placeholder="Parts (R)">
<button class="btn btn-green" onclick="createInvoice()">Save</button>
<button class="btn btn-dark" onclick="hideForm('invForm')">Cancel</button>
</div>
</div>
<div id="invList"><div class="loading">Loading...</div></div>
</div>

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
<div id="inventoryList"><div class="loading">Loading...</div></div>
</div>

<div id="staff" class="panel">
<div class="panel-title">👷 Staff</div>
<button class="btn btn-green" onclick="showForm('staffForm')">+ Add Staff</button>
<div id="staffForm" style="display:none">
<div class="card">
<input class="form-input" id="stName" placeholder="Name">
<input class="form-input" id="stRole" placeholder="Role">
<input class="form-input" id="stPhone" placeholder="Phone">
<input class="form-input" id="stEmail" placeholder="Email">
<input class="form-input" id="stRate" type="number" placeholder="Hourly rate R" value="150">
<button class="btn btn-green" onclick="addStaff()">Save</button>
<button class="btn btn-dark" onclick="hideForm('staffForm')">Cancel</button>
</div>
</div>
<div id="staffList"><div class="loading">Loading...</div></div>
</div>

<div id="expenses" class="panel">
<div class="panel-title">💸 Expenses</div>
<button class="btn btn-green" onclick="showForm('expForm')">+ Add Expense</button>
<div id="expForm" style="display:none">
<div class="card">
<select class="form-input" id="exCat"><option>Rent</option><option>Utilities</option><option>Tools</option><option>Parts</option><option>Salaries</option><option>Fuel</option><option>Marketing</option><option>Other</option></select>
<input class="form-input" id="exAmount" type="number" placeholder="Amount R">
<input class="form-input" id="exDate" type="date">
<textarea class="form-input" id="exNote" placeholder="Note" rows="2"></textarea>
<button class="btn btn-green" onclick="addExpense()">Save</button>
<button class="btn btn-dark" onclick="hideForm('expForm')">Cancel</button>
</div>
</div>
<div id="expenseList"><div class="loading">Loading...</div></div>
</div>

<div id="settings" class="panel">
<div class="panel-title">⚙️ Settings</div>
<div class="card">
<h3>🏢 Workshop Details</h3>
<input class="form-input" id="sLogo" placeholder="🔧" maxlength="4">
<input class="form-input" id="sName" placeholder="Workshop name">
<input class="form-input" id="sPhone" placeholder="Phone">
<input class="form-input" id="sEmail" placeholder="Email">
<input class="form-input" id="sAddress" placeholder="Address">
<input class="form-input" id="sHours" placeholder="Trading hours">
<input class="form-input" id="sRate" type="number" placeholder="Labour rate R/hr">
<h3 style="margin-top:16px">🧾 Business Registration</h3>
<input class="form-input" id="sVat" placeholder="VAT number">
<input class="form-input" id="sCompany" placeholder="Company reg number">
<input class="form-input" id="sBank" placeholder="Bank details (Bank, Account, Branch)">
<h3 style="margin-top:16px">📜 Terms & Conditions</h3>
<textarea class="form-input" id="sTerms" placeholder="Payment terms, warranties..." rows="5"></textarea>
<button class="btn btn-green" onclick="saveSettings()">Save All</button>
</div>
</div>

<div class="bottom-nav">
<div class="bnav active" onclick="showTab('home',this)"><div class="bnav-icon">🏠</div><div class="bnav-label">Home</div></div>
<div class="bnav" onclick="showTab('chat',this)"><div class="bnav-icon">🤖</div><div class="bnav-label">AI</div></div>
<div class="bnav" onclick="showTab('jobs',this)"><div class="bnav-icon">📋</div><div class="bnav-label">Jobs</div></div>
<div class="bnav" onclick="showTab('specs',this)"><div class="bnav-icon">🔧</div><div class="bnav-label">Specs</div></div>
<div class="bnav" onclick="showTab('settings',this)"><div class="bnav-icon">⚙️</div><div class="bnav-label">More</div></div>
</div>

<script>
async function jget(u){const r=await fetch(u);return r.json();}
async function jpost(u,b){const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json();}
async function jput(u,b){const r=await fetch(u,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json();}
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML;}
function showTab(name,el){
document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('.bnav').forEach(t=>t.classList.remove('active'));
document.getElementById(name).classList.add('active');
if(el&&el.classList)el.classList.add('active');
window.scrollTo(0,0);
const L={codes:()=>!document.getElementById('codeResults').dataset.loaded&&searchCodes(),jobs:()=>{loadJobs();loadStaffDropdown();loadBookTimes();},quotes:()=>{loadQuotes();loadBookTimes();},appointments:loadAppts,customers:loadCust,invoices:()=>{loadInv();loadBookTimes();},inventory:loadInventory,staff:loadStaff,expenses:loadExpenses,settings:loadSettings,dashboard:loadDash,analytics:loadAnalytics,warranty:loadWarranty,tax:loadTax,torque:loadTorque,bulbs:loadBulbs,batteries:loadBatt,tyres:loadTyre,wiring:loadWiring,obd:loadOBD,specs:loadSpecs,intervals:loadIntervals,booktime:loadBookTime, suppliers:loadSuppliers};
if(L[name])try{L[name]();}catch(e){console.error(e);}
}
function showForm(id){document.getElementById(id).style.display='block';}
function hideForm(id){document.getElementById(id).style.display='none';}
async function checkStatus(){try{const r=await fetch('/health');const d=await r.json();const db=d.database==='supabase'?' ✓ DB':' ⚠ Memory';document.getElementById('status').innerHTML='<span class="status-online">Backend Online'+db+'</span>';}catch(e){document.getElementById('status').innerHTML='<span class="status-offline">Offline</span>';}}
checkStatus();
function compressImage(f,mw,q){return new Promise((res)=>{const r=new FileReader();r.onload=(e)=>{const img=new Image();img.onload=()=>{const c=document.createElement('canvas');let{width,height}=img;if(width>mw){height=(height*mw)/width;width=mw;}c.width=width;c.height=height;c.getContext('2d').drawImage(img,0,0,width,height);res(c.toDataURL('image/jpeg',q));};img.src=e.target.result;};r.readAsDataURL(f);});}

// SPECS
let specsData=[];
async function loadSpecs(){if(!specsData.length){const d=await jget('/api/specs');specsData=d.specs;}filterSpecs();}
function filterSpecs(){const q=(document.getElementById('specsSearch').value||'').toLowerCase();const f=specsData.filter(x=>!q||x.v.toLowerCase().includes(q));document.getElementById('specsList').innerHTML=f.length?f.map(s=>'<div class="card"><h3>🔧 '+esc(s.v)+'</h3><div class="list-item"><strong>Engine Code:</strong> '+esc(s.engine_code)+'</div><div class="list-item"><strong>Oil:</strong> '+esc(s.oil)+'</div><div class="list-item"><strong>Coolant:</strong> '+esc(s.coolant)+'</div><div class="list-item"><strong>Brake Fluid:</strong> '+esc(s.brake)+'</div><div class="list-item"><strong>Transmission:</strong> '+esc(s.trans)+'</div><div class="list-item"><strong>Firing Order:</strong> '+esc(s.firing)+'</div><div class="list-item"><strong>Timing:</strong> '+esc(s.timing)+'</div></div>').join(''):'<div class="card"><p>No match</p></div>';}

// INTERVALS
let intData=[];
async function loadIntervals(){if(!intData.length){const d=await jget('/api/intervals');intData=d.intervals;}filterIntervals();}
function filterIntervals(){const q=(document.getElementById('intervalSearch').value||'').toLowerCase();const f=intData.filter(x=>!q||x.t.toLowerCase().includes(q));document.getElementById('intervalList').innerHTML=f.map(s=>'<div class="card"><h3>⏰ '+esc(s.t)+'</h3><div class="list-item"><strong>Every:</strong> '+s.km+' km / '+s.months+' months</div><p style="margin-top:8px"><strong>Replace/Check:</strong></p>'+s.items.map(i=>'<div class="list-item">• '+esc(i)+'</div>').join('')+'</div>').join('');}

// BOOK TIME
let bookData=[];
async function loadBookTime(){if(!bookData.length){const d=await jget('/api/book-times');bookData=d.times;}filterBook();}
async function loadBookTimes(){if(!bookData.length){try{const d=await jget('/api/book-times');bookData=d.times;}catch(e){return;}}
const sq=document.getElementById('qBookTime');if(sq)sq.innerHTML='<option value="">— Pick job —</option>'+bookData.map(b=>'<option value="'+b.hrs+'">'+esc(b.job)+' ('+b.hrs+'h)</option>').join('');
const si=document.getElementById('iBookTime');if(si)si.innerHTML='<option value="">— Pick job —</option>'+bookData.map(b=>'<option value="'+b.hrs+'">'+esc(b.job)+' ('+b.hrs+'h)</option>').join('');
}
function filterBook(){const q=(document.getElementById('bookSearch').value||'').toLowerCase();const f=bookData.filter(x=>!q||x.job.toLowerCase().includes(q));document.getElementById('bookList').innerHTML=f.map(b=>'<div class="card"><h3>⏱️ '+esc(b.job)+'</h3><div class="list-item"><strong>Standard time:</strong> '+b.hrs+' hours</div></div>').join('');}
async function applyBookTime(){const h=parseFloat(document.getElementById('qBookTime').value)||0;if(!h)return;const rate=await getRate();document.getElementById('qLabour').value=(h*rate).toFixed(2);}
async function applyInvBookTime(){const h=parseFloat(document.getElementById('iBookTime').value)||0;if(!h)return;const rate=await getRate();document.getElementById('iLabour').value=(h*rate).toFixed(2);}
async function getRate(){try{const r=await jget('/api/workshop');return r.labour_rate||450;}catch(e){return 450;}}

// SUPPLIERS
async function loadSuppliers(){
const c=document.getElementById('supplierList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/suppliers');
c.innerHTML=d.suppliers.length?d.suppliers.map(s=>'<div class="card"><h3>📞 '+esc(s.name)+'</h3>'+(s.category?'<p style="font-size:12px;color:var(--text2)">'+esc(s.category)+'</p>':'')+(s.phone?'<p>📞 '+esc(s.phone)+'</p>':'')+(s.email?'<p>📧 '+esc(s.email)+'</p>':'')+(s.account_number?'<p>Account: '+esc(s.account_number)+'</p>':'')+(s.notes?'<p style="font-size:12px;color:var(--text2)">'+esc(s.notes)+'</p>':'')+'<div style="margin-top:8px">'+(s.phone?'<button class="btn-sm blue" onclick="window.location.href=\'tel:'+esc(s.phone)+'\'">📞 Call</button>':'')+(s.whatsapp?'<button class="btn-sm wa" onclick="window.open(\'https://wa.me/'+esc(s.whatsapp).replace(/\D/g,'')+'\',\'_blank\')">📱 WhatsApp</button>':'')+'<button class="btn-sm red" onclick="delSupplier(\''+s.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No suppliers yet</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}}
async function addSupplier(){const n=document.getElementById('supName').value.trim();if(!n){alert('Name required');return;}
await jpost('/api/suppliers',{name:n,phone:document.getElementById('supPhone').value,email:document.getElementById('supEmail').value,whatsapp:document.getElementById('supWhatsapp').value,category:document.getElementById('supCategory').value,account_number:document.getElementById('supAccount').value,notes:document.getElementById('supNotes').value});
['supName','supPhone','supEmail','supWhatsapp','supCategory','supAccount','supNotes'].forEach(id=>document.getElementById(id).value='');
hideForm('supplierForm');loadSuppliers();}
async function delSupplier(id){if(!confirm('Delete?'))return;await fetch('/api/suppliers/'+id,{method:'DELETE'});loadSuppliers();}

// VIN
async function decodeVin(){const vin=document.getElementById('vinInput').value.trim().toUpperCase();const c=document.getElementById('vinResult');
if(vin.length!==17){c.innerHTML='<div class="card"><p style="color:#ef4444">17 chars required</p></div>';return;}
c.innerHTML='<div class="loading">...</div>';
try{const d=await jget('/api/vin/'+vin);if(d.detail){c.innerHTML='<div class="card"><p style="color:#ef4444">'+d.detail+'</p></div>';return;}
c.innerHTML='<div class="card"><h3>🔍 Info</h3><p><strong>VIN:</strong> '+d.vin+'</p><p><strong>Manufacturer:</strong> '+d.manufacturer+'</p><p><strong>Country:</strong> '+d.country+'</p><p><strong>Year:</strong> '+d.year+'</p><p><strong>Plant:</strong> '+d.plant+'</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}}

// PHOTO
let diagB64='';
async function previewDiag(e){const f=e.target.files[0];if(!f)return;diagB64=await compressImage(f,1200,0.75);document.getElementById('photoPreview').innerHTML='<img class="img-preview" src="'+diagB64+'">';}
async function diagnosePhoto(){const btn=document.getElementById('photoBtn');const c=document.getElementById('photoResult');
if(!diagB64){c.innerHTML='<div class="card"><p style="color:#ef4444">Select photo</p></div>';return;}
btn.disabled=true;btn.textContent='📸 Analyzing...';c.innerHTML='<div class="loading">...</div>';
try{const d=await jpost('/api/diagnose/photo',{image_base64:diagB64,vehicle_info:document.getElementById('photoVehicle').value});
if(!d.success){c.innerHTML='<div class="card"><p style="color:#ef4444">'+(d.error||'Failed')+'</p></div>';}
else{let h='<div class="card"><h3>🔍 '+(d.problem?esc(d.problem):'Detected')+'</h3><p><strong>Confidence:</strong> '+(d.confidence||'?')+'</p>'+(d.description?'<p style="margin-top:8px">'+esc(d.description)+'</p>':'')+'</div>';
if(d.possible_causes)h+='<div class="card"><h3>Causes</h3>'+d.possible_causes.map(x=>'<div class="list-item">• '+esc(x)+'</div>').join('')+'</div>';
if(d.diagnostic_steps)h+='<div class="card"><h3>Steps</h3>'+d.diagnostic_steps.map(x=>'<div class="list-item">• '+esc(x)+'</div>').join('')+'</div>';
if(d.safety_warnings)h+='<div class="card" style="background:#fef2f2"><h3 style="color:#dc2626">⚠️ Safety</h3>'+d.safety_warnings.map(x=>'<div class="list-item">⚠ '+esc(x)+'</div>').join('')+'</div>';
c.innerHTML=h;}}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
btn.disabled=false;btn.textContent='📸 Analyze';}

// PAINT
let paintB64='';
async function previewPaint(e){const f=e.target.files[0];if(!f)return;paintB64=await compressImage(f,1200,0.75);document.getElementById('paintPreview').innerHTML='<img class="img-preview" src="'+paintB64+'">';}
async function matchPaint(){const btn=document.getElementById('paintBtn');const c=document.getElementById('paintResult');
if(!paintB64){c.innerHTML='<div class="card"><p style="color:#ef4444">Select photo</p></div>';return;}
btn.disabled=true;btn.textContent='🎨 Analyzing...';c.innerHTML='<div class="loading">...</div>';
try{const d=await jpost('/api/paint/match',{image_base64:paintB64,vehicle_info:document.getElementById('paintVehicle').value});
if(!d.success){c.innerHTML='<div class="card"><p style="color:#ef4444">'+(d.error||'Failed')+'</p></div>';}
else{const col=d.detected_colour||{};let h='<div class="card"><div class="swatch" style="background:'+(col.hex_code||'#ccc')+'"></div><h3>'+esc(col.name||'Unknown')+'</h3><p><strong>'+esc(col.finish||'')+'</strong>'+(col.colour_family?' • '+esc(col.colour_family):'')+'</p><p style="font-family:monospace">'+(col.hex_code||'')+'</p><p>Confidence: <strong>'+(d.confidence||'?')+'</strong></p></div>';
if(d.brand_codes){h+='<div class="card"><h3>Brand Codes</h3>';d.brand_codes.forEach(b=>{h+='<div class="list-item"><strong>'+esc(b.brand)+':</strong> '+esc(b.code||'?')+'</div>';});h+='</div>';}
c.innerHTML=h;}}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
btn.disabled=false;btn.textContent='🎨 Match Colour';}

// TORQUE
let torqueData=[],seqData=[];
async function loadTorque(){if(!torqueData.length){const d=await jget('/api/torque');torqueData=d.bolts;seqData=d.sequences;}filterTorque();}
function filterTorque(){const q=(document.getElementById('torqueSearch').value||'').toLowerCase();const f=torqueData.filter(x=>!q||x.s.toLowerCase().includes(q)||x.g.toLowerCase().includes(q));document.getElementById('torqueTable').innerHTML='<table class="torque-table"><tr><th>Size</th><th>Grade</th><th>Nm</th><th>ft·lb</th><th>Use</th></tr>'+f.map(x=>'<tr><td><strong>'+esc(x.s)+'</strong></td><td>'+esc(x.g)+'</td><td>'+x.nm+'</td><td>'+x.ft+'</td><td>'+esc(x.u)+'</td></tr>').join('')+'</table>';
document.getElementById('torqueSeq').innerHTML=seqData.map(s=>'<div class="card"><h3>'+esc(s.c)+'</h3>'+s.st.map(x=>'<div class="list-item">• '+esc(x)+'</div>').join('')+'</div>').join('');}

// BOLT CALC
async function calcTorque(){const d=await jpost('/api/bolt-calc',{size:document.getElementById('boltSize').value,grade:document.getElementById('boltGrade').value,condition:document.getElementById('boltCondition').value});
document.getElementById('boltResult').innerHTML='<div class="card" style="background:linear-gradient(135deg,#667eea,#764ba2);color:white"><h3 style="color:white">Torque</h3><p style="font-size:32px;font-weight:800;color:white">'+d.nm.toFixed(1)+' Nm</p><p style="color:white">'+d.ftlb.toFixed(1)+' ft·lb</p></div>';}

// BULBS/BATT/TYRES/WIRING/OBD
let bulbsData=[],battData=[],tyreData=[],wiringData=[],obdData=[];
async function loadBulbs(){if(!bulbsData.length){const d=await jget('/api/bulbs');bulbsData=d.bulbs;}filterBulbs();}
function filterBulbs(){const q=(document.getElementById('bulbSearch').value||'').toLowerCase();const f=bulbsData.filter(x=>!q||x.v.toLowerCase().includes(q));document.getElementById('bulbList').innerHTML=f.map(b=>'<div class="card"><h3>💡 '+esc(b.v)+'</h3><div class="list-item">Low: <strong>'+esc(b.l)+'</strong></div><div class="list-item">High: <strong>'+esc(b.h)+'</strong></div><div class="list-item">Fog: <strong>'+esc(b.f)+'</strong></div><div class="list-item">Rev: <strong>'+esc(b.r)+'</strong></div></div>').join('');}
async function loadBatt(){if(!battData.length){const d=await jget('/api/batteries');battData=d.batteries;}filterBatt();}
function filterBatt(){const q=(document.getElementById('battSearch').value||'').toLowerCase();const f=battData.filter(x=>!q||x.v.toLowerCase().includes(q));document.getElementById('battList').innerHTML=f.map(b=>'<div class="card"><h3>🔋 '+esc(b.v)+'</h3><div class="list-item">Group: <strong>'+esc(b.g)+'</strong></div><div class="list-item">CCA: <strong>'+b.c+'</strong></div><div class="list-item">Ah: <strong>'+b.a+'</strong></div></div>').join('');}
async function loadTyre(){if(!tyreData.length){const d=await jget('/api/tyres');tyreData=d.tyres;}filterTyre();}
function filterTyre(){const q=(document.getElementById('tyreSearch').value||'').toLowerCase();const f=tyreData.filter(x=>!q||x.v.toLowerCase().includes(q));document.getElementById('tyreList').innerHTML=f.map(t=>'<div class="card"><h3>🛞 '+esc(t.v)+'</h3><div class="list-item">Size: <strong>'+esc(t.s)+'</strong></div><div class="list-item">Front: <strong>'+esc(t.f)+'</strong></div><div class="list-item">Rear: <strong>'+esc(t.r)+'</strong></div></div>').join('');}
async function loadWiring(){if(!wiringData.length){const d=await jget('/api/wiring');wiringData=d.circuits;}filterWiring();}
function filterWiring(){const q=(document.getElementById('wiringSearch').value||'').toLowerCase();const f=wiringData.filter(x=>!q||x.n.toLowerCase().includes(q)||x.sy.toLowerCase().includes(q));document.getElementById('wiringList').innerHTML=f.map(w=>'<div class="card"><h3>🔌 '+esc(w.n)+'</h3><p style="font-size:12px;color:var(--text2)">'+esc(w.sy)+'</p><p><strong>Components:</strong></p>'+w.c.map(c=>'<div class="list-item">• '+esc(c)+'</div>').join('')+'<p><strong>Connections:</strong></p>'+w.co.map(c=>'<div class="list-item" style="font-family:monospace;font-size:11px">'+esc(c)+'</div>').join('')+'</div>').join('');}
async function loadOBD(){if(!obdData.length){const d=await jget('/api/obd-pids');obdData=d.pids;}filterOBD();}
function filterOBD(){const q=(document.getElementById('obdSearch').value||'').toLowerCase();const f=obdData.filter(x=>!q||x.n.toLowerCase().includes(q)||x.p.includes(q));document.getElementById('obdList').innerHTML='<table class="torque-table"><tr><th>PID</th><th>Name</th><th>Desc</th></tr>'+f.map(x=>'<tr><td><strong>'+x.p+'</strong></td><td>'+esc(x.n)+'</td><td style="font-size:11px">'+esc(x.d)+'</td></tr>').join('')+'</table>';}

async function sendMsg(){const i=document.getElementById('chatInput');const m=i.value.trim();if(!m)return;const b=document.getElementById('chatBox');b.innerHTML+='<div class="msg user">'+esc(m)+'</div>';i.value='';b.scrollTop=b.scrollHeight;b.innerHTML+='<div class="msg ai" id="typ">...</div>';b.scrollTop=b.scrollHeight;try{const d=await jpost('/api/chat',{message:m});document.getElementById('typ').outerHTML='<div class="msg ai">'+esc(d.reply)+'</div>';}catch(e){document.getElementById('typ').outerHTML='<div class="msg ai">Error</div>';}b.scrollTop=b.scrollHeight;}

async function loadDash(){try{const d=await jget('/api/stats');document.getElementById('dashStats').innerHTML='<div class="stats-row"><div class="stat-card blue"><div class="num">'+d.jobs_total+'</div><div class="lbl">Jobs</div></div><div class="stat-card purple"><div class="num">'+d.jobs_open+'</div><div class="lbl">Open</div></div><div class="stat-card green"><div class="num">'+d.jobs_completed+'</div><div class="lbl">Done</div></div><div class="stat-card"><div class="num">'+d.customers+'</div><div class="lbl">Customers</div></div><div class="stat-card green"><div class="num">R'+d.revenue+'</div><div class="lbl">Rev</div></div><div class="stat-card red"><div class="num">R'+d.expenses+'</div><div class="lbl">Exp</div></div></div>';
if(window._rC)window._rC.destroy();const c1=document.getElementById('revenueChart');if(c1)window._rC=new Chart(c1,{type:'line',data:{labels:d.revenue_labels,datasets:[{data:d.revenue_data,borderColor:'#667eea',backgroundColor:'rgba(102,126,234,.15)',tension:.4,fill:true,borderWidth:3}]},options:{responsive:true,plugins:{legend:{display:false}}}});
if(window._jC)window._jC.destroy();const c2=document.getElementById('jobChart');if(c2)window._jC=new Chart(c2,{type:'doughnut',data:{labels:['New','Progress','Done'],datasets:[{data:[d.jobs_new,d.jobs_progress,d.jobs_completed],backgroundColor:['#6b7280','#f59e0b','#10b981']}]},options:{responsive:true}});
const ls=await jget('/api/inventory/low-stock');document.getElementById('dashLowStock').innerHTML=ls.items.length?ls.items.map(i=>'<div class="list-item">⚠️ <strong>'+esc(i.name)+'</strong> — '+i.qty+' left</div>').join(''):'<p style="color:var(--text2)">All OK</p>';}catch(e){}}

async function loadAnalytics(){try{const d=await jget('/api/analytics');let h='<div class="stats-row"><div class="stat-card blue"><div class="num">R'+d.avg_invoice.toFixed(0)+'</div><div class="lbl">Avg Inv</div></div><div class="stat-card green"><div class="num">R'+d.total_revenue.toFixed(0)+'</div><div class="lbl">Revenue</div></div></div>';
if(d.top_services.length){h+='<div class="card"><h3>🔥 Top Jobs</h3>';d.top_services.forEach(s=>{h+='<div class="list-item"><strong>'+esc(s.name)+'</strong> — '+s.count+'×</div>';});h+='</div>';}
if(d.top_customers.length){h+='<div class="card"><h3>⭐ Customers</h3>';d.top_customers.forEach(x=>{h+='<div class="list-item"><strong>'+esc(x.name)+'</strong> — R'+x.total.toFixed(0)+'</div>';});h+='</div>';}
document.getElementById('analyticsContent').innerHTML=h;}catch(e){}}

async function loadWarranty(){const c=document.getElementById('warrantyList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/warranty');c.innerHTML=d.warranties.length?d.warranties.map(w=>'<div class="card"><h3>🎁 '+esc(w.vehicle)+' <span class="badge '+(w.status==='active'?'ok':'warn')+'">'+w.status+'</span></h3><p><strong>'+esc(w.customer)+'</strong></p><div class="list-item">Expires: '+esc(w.expiry)+'</div><div class="list-item">'+(w.days_left>0?w.days_left+' days':'Expired')+'</div></div>').join(''):'<div class="card"><p>None</p></div>';}catch(e){}}

async function loadTax(){try{const d=await jget('/api/workshop');const n=new Date();const f=new Date(n.getFullYear(),n.getMonth(),1);document.getElementById('taxFrom').value=f.toISOString().slice(0,10);document.getElementById('taxTo').value=n.toISOString().slice(0,10);}catch(e){}}
function downloadTax(){const f=document.getElementById('taxFrom').value;const t=document.getElementById('taxTo').value;if(!f||!t){alert('Select dates');return;}window.location.href='/api/export/tax?from_date='+f+'&to_date='+t;}

async function searchCodes(){const q=document.getElementById('codeSearch').value;const c=document.getElementById('codeResults');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/fault-codes?search='+encodeURIComponent(q));c.dataset.loaded='1';c.innerHTML=d.codes.length?d.codes.map(x=>'<div class="card"><h3>'+x.code+'<span class="badge '+x.severity.toLowerCase()+'">'+x.severity+'</span></h3><p><strong>'+esc(x.description)+'</strong></p><p style="color:var(--text2);font-size:12px">'+esc(x.system)+'</p><p><strong>Causes:</strong></p>'+x.causes.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'<p><strong>Steps:</strong></p>'+x.steps.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'</div>').join(''):'<div class="card"><p>None</p></div>';}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}}

// JOBS
let jobBeforePhotos=[],jobAfterPhotos=[];
async function addPhoto(e,type){const arr=type==='before'?jobBeforePhotos:jobAfterPhotos;for(const f of Array.from(e.target.files)){arr.push(await compressImage(f,1000,0.7));}renderPhotos();}
function renderPhotos(){document.getElementById('beforeRow').innerHTML=jobBeforePhotos.map((p,i)=>'<div style="position:relative"><img class="photo-thumb" src="'+p+'"><button class="btn-sm red" style="position:absolute;top:-5px;right:-5px;width:24px;height:24px;padding:0" onclick="jobBeforePhotos.splice('+i+',1);renderPhotos()">×</button></div>').join('');}
function resetJobPhotos(){jobBeforePhotos=[];jobAfterPhotos=[];renderPhotos();}
async function loadStaffDropdown(){try{const d=await jget('/api/staff');const sel=document.getElementById('jAssigned');if(sel)sel.innerHTML='<option value="">— Assign —</option>'+d.staff.map(s=>'<option value="'+esc(s.name)+'">'+esc(s.name)+'</option>').join('');}catch(e){}}
async function loadJobs(){const c=document.getElementById('jobList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/jobs');c.innerHTML=d.jobs.length?d.jobs.map(j=>{let ph=(j.photos_before&&j.photos_before.length)?'<div class="photo-row">'+j.photos_before.map(p=>'<img class="photo-thumb" src="'+p+'">').join('')+'</div>':'';return '<div class="card"><h3>Job #'+j.id+' <span class="badge '+j.status.toLowerCase().replace(' ','')+'">'+j.status+'</span></h3><p><strong>'+esc(j.customer)+'</strong></p><p>🚗 '+esc(j.vehicle)+'</p>'+(j.assigned_to?'<p style="color:var(--text2);font-size:12px">👷 '+esc(j.assigned_to)+'</p>':'')+'<p style="color:var(--text2)">'+esc(j.complaint)+'</p>'+ph+'<div style="margin-top:8px"><button class="btn-sm blue" onclick="upJob(\''+j.id+'\',\'In Progress\')">Progress</button><button class="btn-sm green" onclick="upJob(\''+j.id+'\',\'Completed\')">Done</button><button class="btn-sm wa" onclick="waJob(\''+j.id+'\')">📱</button><button class="btn-sm red" onclick="delJob(\''+j.id+'\')">×</button></div></div>';}).join(''):'<div class="card"><p>No jobs</p></div>';}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}}
async function createJob(){const c=document.getElementById('jCustomer').value.trim();const v=document.getElementById('jVehicle').value.trim();const comp=document.getElementById('jComplaint').value.trim();if(!c||!v||!comp){alert('Fill required');return;}
await jpost('/api/jobs',{customer:c,phone:document.getElementById('jPhone').value,vehicle:v,registration:document.getElementById('jReg').value,complaint:comp,assigned_to:document.getElementById('jAssigned').value,warranty_months:parseInt(document.getElementById('jWarranty').value)||6,photos_before:jobBeforePhotos});
['jCustomer','jPhone','jVehicle','jReg','jComplaint'].forEach(id=>document.getElementById(id).value='');resetJobPhotos();hideForm('jobForm');loadJobs();}
async function upJob(id,s){await jput('/api/jobs/'+id,{status:s});loadJobs();}
async function delJob(id){if(!confirm('Delete?'))return;await fetch('/api/jobs/'+id,{method:'DELETE'});loadJobs();}
function waJob(id){jget('/api/jobs').then(d=>{const j=d.jobs.find(x=>x.id==id);if(!j)return;const txt='🔧 Job #'+j.id+'\n'+j.customer+'\n'+j.vehicle+'\nStatus: '+j.status;window.open('https://wa.me/?text='+encodeURIComponent(txt),'_blank');});}

// QUOTES
async function loadQuotes(){const c=document.getElementById('quoteList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/quotes');c.innerHTML=d.quotes.length?d.quotes.map(q=>'<div class="card"><h3>💬 Quote #'+q.id+'</h3><p><strong>'+esc(q.customer)+'</strong></p><p>'+esc(q.description)+'</p><div class="list-item"><strong>Total: R'+q.total.toFixed(2)+'</strong></div><div style="margin-top:8px"><button class="btn-sm green" onclick="acceptQuote(\''+q.id+'\')">→ Inv</button><button class="btn-sm red" onclick="delQuote(\''+q.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No quotes</p></div>';}catch(e){}}
async function createQuote(){const c=document.getElementById('qCustomer').value.trim();const d=document.getElementById('qDesc').value.trim();if(!c||!d){alert('Required');return;}await jpost('/api/quotes',{customer:c,vehicle:document.getElementById('qVehicle').value,description:d,labour:parseFloat(document.getElementById('qLabour').value)||0,parts:parseFloat(document.getElementById('qParts').value)||0});['qCustomer','qVehicle','qDesc','qLabour','qParts'].forEach(id=>document.getElementById(id).value='');hideForm('quoteForm');loadQuotes();}
async function acceptQuote(id){if(!confirm('Convert?'))return;const r=await jpost('/api/quotes/'+id+'/accept',{});if(r.success){alert('Converted');loadQuotes();}}
async function delQuote(id){if(!confirm('Delete?'))return;await fetch('/api/quotes/'+id,{method:'DELETE'});loadQuotes();}

// APPTS
async function loadAppts(){const c=document.getElementById('apptList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/appointments');const s=d.appointments.sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time));c.innerHTML=s.length?s.map(a=>'<div class="card"><h3>📅 '+esc(a.date)+' '+esc(a.time)+'</h3><p><strong>'+esc(a.customer)+'</strong></p><button class="btn-sm red" onclick="delAppt(\''+a.id+'\')">Delete</button></div>').join(''):'<div class="card"><p>None</p></div>';}catch(e){}}
async function createAppt(){const c=document.getElementById('aCustomer').value.trim();const d=document.getElementById('aDate').value;const t=document.getElementById('aTime').value;if(!c||!d||!t){alert('Required');return;}await jpost('/api/appointments',{customer:c,phone:document.getElementById('aPhone').value,vehicle:document.getElementById('aVehicle').value,service:document.getElementById('aService').value,date:d,time:t});['aCustomer','aPhone','aVehicle','aService','aDate','aTime'].forEach(id=>document.getElementById(id).value='');hideForm('apptForm');loadAppts();}
async function delAppt(id){if(!confirm('Delete?'))return;await fetch('/api/appointments/'+id,{method:'DELETE'});loadAppts();}

// CUSTOMERS
async function loadCust(){const c=document.getElementById('custList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/customers');c.innerHTML=d.customers.length?d.customers.map(x=>'<div class="card"><h3>👤 '+esc(x.name)+'</h3><p>📞 '+esc(x.phone)+'</p>'+(x.email?'<p>📧 '+esc(x.email)+'</p>':'')+'<button class="btn-sm wa" onclick="waCust(\''+esc(x.phone)+'\')">📱</button><button class="btn-sm red" onclick="delCust(\''+x.id+'\')">×</button></div>').join(''):'<div class="card"><p>None</p></div>';}catch(e){}}
async function createCustomer(){const n=document.getElementById('cName').value.trim();const p=document.getElementById('cPhone').value.trim();if(!n||!p){alert('Required');return;}await jpost('/api/customers',{name:n,phone:p,email:document.getElementById('cEmail').value});['cName','cPhone','cEmail'].forEach(id=>document.getElementById(id).value='');hideForm('custForm');loadCust();}
async function delCust(id){if(!confirm('Delete?'))return;await fetch('/api/customers/'+id,{method:'DELETE'});loadCust();}
function waCust(p){window.open('https://wa.me/'+p.replace(/\D/g,''),'_blank');}

// INVOICES
async function loadInv(){const c=document.getElementById('invList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/invoices');c.innerHTML=d.invoices.length?d.invoices.map(i=>'<div class="card" id="inv-'+i.id+'"><h3>Inv #'+i.id+'</h3><p><strong>'+esc(i.customer)+'</strong></p><p>'+esc(i.description)+'</p><div class="list-item"><strong>Total: R'+i.total.toFixed(2)+'</strong></div><div style="margin-top:8px"><button class="btn-sm wa" onclick="waInv(\''+i.id+'\')">📱</button><button class="btn-sm blue" onclick="printInv(\''+i.id+'\')">🖨</button><button class="btn-sm red" onclick="delInv(\''+i.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>None</p></div>';}catch(e){}}
async function createInvoice(){const c=document.getElementById('iCustomer').value.trim();const d=document.getElementById('iDesc').value.trim();if(!c||!d){alert('Required');return;}await jpost('/api/invoices',{customer:c,vehicle:document.getElementById('iVehicle').value,description:d,labour:parseFloat(document.getElementById('iLabour').value)||0,parts:parseFloat(document.getElementById('iParts').value)||0});['iCustomer','iVehicle','iDesc','iLabour','iParts'].forEach(id=>document.getElementById(id).value='');hideForm('invForm');loadInv();}
async function delInv(id){if(!confirm('Delete?'))return;await fetch('/api/invoices/'+id,{method:'DELETE'});loadInv();}
function waInv(id){jget('/api/invoices').then(d=>{const i=d.invoices.find(x=>x.id==id);if(!i)return;const txt='💰 Invoice #'+i.id+'\n'+i.customer+'\nTotal: R'+i.total.toFixed(2);window.open('https://wa.me/?text='+encodeURIComponent(txt),'_blank');});}
function printInv(id){jget('/api/invoices').then(d=>{const i=d.invoices.find(x=>x.id==id);const w=window.open('','','width=800,height=600');w.document.write('<html><head><title>Invoice #'+i.id+'</title><style>body{font-family:Arial;padding:20px;max-width:600px;margin:auto}h1{color:#E65100;border-bottom:2px solid #E65100;padding-bottom:8px}h2{color:#333}.row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #eee}.total{font-size:20px;font-weight:bold;color:#E65100;border-top:2px solid #E65100;padding-top:8px}.terms{margin-top:24px;font-size:11px;color:#666;border-top:1px dashed #ccc;padding-top:12px}</style></head><body>');
Promise.all([fetch('/api/workshop').then(r=>r.json())]).then(([ws])=>{
w.document.write('<h1>'+(ws.logo||'🔧')+' '+esc(ws.name||'Workshop')+'</h1>');
w.document.write('<p>'+esc(ws.phone||'')+' | '+esc(ws.email||'')+'<br>'+esc(ws.address||'')+'<br>'+(ws.vat_number?'VAT: '+esc(ws.vat_number)+' | ':'')+(ws.company_reg?'Reg: '+esc(ws.company_reg):'')+'</p>');
w.document.write('<h2>Invoice #'+i.id+'</h2>');
w.document.write('<p><strong>Customer:</strong> '+esc(i.customer)+'<br><strong>Vehicle:</strong> '+esc(i.vehicle||'-')+'</p>');
w.document.write('<div class="row"><span>'+esc(i.description)+'</span><span></span></div>');
w.document.write('<div class="row"><span>Labour</span><span>R'+i.labour.toFixed(2)+'</span></div>');
w.document.write('<div class="row"><span>Parts</span><span>R'+i.parts.toFixed(2)+'</span></div>');
w.document.write('<div class="row"><span>Subtotal</span><span>R'+i.subtotal.toFixed(2)+'</span></div>');
w.document.write('<div class="row"><span>VAT (15%)</span><span>R'+i.vat.toFixed(2)+'</span></div>');
w.document.write('<div class="row total"><span>TOTAL</span><span>R'+i.total.toFixed(2)+'</span></div>');
if(ws.bank_details)w.document.write('<p><strong>Bank:</strong> '+esc(ws.bank_details)+'</p>');
w.document.write('<div class="terms"><strong>Terms & Conditions:</strong><br>'+esc(ws.terms||'Payment due within 30 days.')+'</div>');
w.document.write('</body></html>');w.document.close();setTimeout(()=>w.print(),500);});});}

// INVENTORY
async function loadInventory(){const c=document.getElementById('inventoryList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/inventory');c.innerHTML=d.items.length?d.items.map(i=>{const cls=i.qty<=i.min_qty?'warn':'ok';return '<div class="card"><h3>'+esc(i.name)+' <span class="badge '+cls+'">'+i.qty+'</span></h3><div class="list-item">Cost R'+i.cost_price.toFixed(2)+' | Sell R'+i.sell_price.toFixed(2)+'</div><div style="margin-top:8px"><button class="btn-sm green" onclick="adjInv(\''+i.id+'\',1)">+1</button><button class="btn-sm red" onclick="adjInv(\''+i.id+'\',-1)">-1</button><button class="btn-sm gray" onclick="delInvItem(\''+i.id+'\')">×</button></div></div>';}).join(''):'<div class="card"><p>None</p></div>';}catch(e){}}
async function addInventory(){const n=document.getElementById('pName').value.trim();if(!n){alert('Name required');return;}await jpost('/api/inventory',{part_number:document.getElementById('pNumber').value,name:n,category:document.getElementById('pCategory').value,qty:parseInt(document.getElementById('pQty').value)||0,min_qty:parseInt(document.getElementById('pMinQty').value)||5,cost_price:parseFloat(document.getElementById('pCost').value)||0,sell_price:parseFloat(document.getElementById('pSell').value)||0,supplier:document.getElementById('pSupplier').value});['pNumber','pName','pCategory','pQty','pMinQty','pCost','pSell','pSupplier'].forEach(id=>document.getElementById(id).value='');hideForm('invItemForm');loadInventory();}
async function adjInv(id,d){await jpost('/api/inventory/'+id+'/adjust',{delta:d});loadInventory();}
async function delInvItem(id){if(!confirm('Delete?'))return;await fetch('/api/inventory/'+id,{method:'DELETE'});loadInventory();}

// STAFF
async function loadStaff(){const c=document.getElementById('staffList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/staff');c.innerHTML=d.staff.length?d.staff.map(s=>'<div class="card"><h3>👷 '+esc(s.name)+'</h3>'+(s.role?'<p>'+esc(s.role)+'</p>':'')+(s.phone?'<p>📞 '+esc(s.phone)+'</p>':'')+'<p>R'+s.hourly_rate.toFixed(2)+'/hr</p><button class="btn-sm red" onclick="delStaff(\''+s.id+'\')">Delete</button></div>').join(''):'<div class="card"><p>None</p></div>';}catch(e){}}
async function addStaff(){const n=document.getElementById('stName').value.trim();if(!n){alert('Name required');return;}await jpost('/api/staff',{name:n,role:document.getElementById('stRole').value,phone:document.getElementById('stPhone').value,email:document.getElementById('stEmail').value,hourly_rate:parseFloat(document.getElementById('stRate').value)||150});['stName','stRole','stPhone','stEmail'].forEach(id=>document.getElementById(id).value='');hideForm('staffForm');loadStaff();}
async function delStaff(id){if(!confirm('Delete?'))return;await fetch('/api/staff/'+id,{method:'DELETE'});loadStaff();}

// EXPENSES
async function loadExpenses(){const c=document.getElementById('expenseList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/expenses');const total=d.expenses.reduce((s,x)=>s+parseFloat(x.amount||0),0);let h='<div class="card" style="background:linear-gradient(135deg,#ef4444,#f87171);color:white"><h3 style="color:white">Total</h3><p style="font-size:26px;color:white;font-weight:800">R'+total.toFixed(2)+'</p></div>';
h+=d.expenses.length?d.expenses.map(e=>'<div class="card"><h3>'+esc(e.category)+' <span class="badge new">R'+parseFloat(e.amount).toFixed(2)+'</span></h3>'+(e.note?'<p>'+esc(e.note)+'</p>':'')+'<button class="btn-sm red" onclick="delExpense(\''+e.id+'\')">×</button></div>').join(''):'<div class="card"><p>None</p></div>';
c.innerHTML=h;}catch(e){}}
async function addExpense(){const a=parseFloat(document.getElementById('exAmount').value)||0;if(!a){alert('Amount required');return;}await jpost('/api/expenses',{category:document.getElementById('exCat').value,amount:a,date:document.getElementById('exDate').value||new Date().toISOString().slice(0,10),note:document.getElementById('exNote').value});['exAmount','exDate','exNote'].forEach(id=>document.getElementById(id).value='');hideForm('expForm');loadExpenses();}
async function delExpense(id){if(!confirm('Delete?'))return;await fetch('/api/expenses/'+id,{method:'DELETE'});loadExpenses();}

// SETTINGS
async function loadSettings(){try{const d=await jget('/api/workshop');document.getElementById('sLogo').value=d.logo||'🔧';document.getElementById('sName').value=d.name||'';document.getElementById('sPhone').value=d.phone||'';document.getElementById('sEmail').value=d.email||'';document.getElementById('sAddress').value=d.address||'';document.getElementById('sHours').value=d.hours||'';document.getElementById('sRate').value=d.labour_rate||450;document.getElementById('sVat').value=d.vat_number||'';document.getElementById('sCompany').value=d.company_reg||'';document.getElementById('sBank').value=d.bank_details||'';document.getElementById('sTerms').value=d.terms||'';applyBrand(d);}catch(e){}}
function applyBrand(d){const logo=d.logo||'🔧';const name=(d.name||'RAMSTECH').toUpperCase();document.querySelector('.header h1').innerHTML=logo+' <span id="wsName">'+name+'</span>';const sub=[d.phone,d.address].filter(Boolean).join(' • ');document.getElementById('wsSub').textContent=sub||'AI Workshop Assistant';}
async function saveSettings(){const p={logo:document.getElementById('sLogo').value||'🔧',name:document.getElementById('sName').value,phone:document.getElementById('sPhone').value,email:document.getElementById('sEmail').value,address:document.getElementById('sAddress').value,hours:document.getElementById('sHours').value,labour_rate:parseFloat(document.getElementById('sRate').value)||450,vat_number:document.getElementById('sVat').value,company_reg:document.getElementById('sCompany').value,bank_details:document.getElementById('sBank').value,terms:document.getElementById('sTerms').value};await jpost('/api/workshop',p);applyBrand(p);alert('Saved ✓');}
loadSettings();
</script>
</body></html>"""

# ═══ ROUTES ═══
@app.get("/", response_class=HTMLResponse)
async def home(): return HTML

@app.get("/health")
def health(): return {"status":"healthy","database":"supabase" if DB_READY else "memory"}

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

@app.get("/api/vin/{vin}")
def decode_vin(vin: str):
    v = vin.strip().upper()
    if len(v) != 17: raise HTTPException(400,"VIN must be exactly 17 characters")
    mfr, country = WMI_DB.get(v[:3], ("Unknown","Unknown"))
    plants = {"A":"Ingolstadt","B":"Brussels","D":"Dingolfing","F":"Flint","H":"Hiroshima","T":"Toyota City","U":"Ulsan","W":"Wolfsburg","Y":"Yokohama"}
    return {"vin":v,"manufacturer":mfr,"country":country,"year":YEAR_CODES.get(v[9],"Unknown"),"plant":plants.get(v[10],"Unknown"),"serial":v[11:]}

@app.post("/api/chat")
async def chat(r: Request):
    d = await r.json(); msg = d.get("message","")
    if not msg: raise HTTPException(400,"Message required")
    if not OPENAI_KEY: return {"reply":"AI not configured"}
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        resp = c.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role":"system","content":"You are RamsTech AI, expert mechanic."},{"role":"user","content":msg}], max_tokens=800, temperature=0.3)
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

@app.get("/api/torque")
def torque(): return {"bolts":TORQUE,"sequences":SEQ}

@app.post("/api/bolt-calc")
async def bolt_calc(r: Request):
    d = await r.json(); size = d.get("size","M8"); grade = d.get("grade","8.8"); cond = d.get("condition","dry")
    tm = {"8.8":800,"10.9":1040,"12.9":1220}; am = {"M6":20.1,"M8":36.6,"M10":58.0,"M12":84.3,"M14":115.0,"M16":157.0,"M20":245.0}; km = {"dry":0.20,"oiled":0.17,"moly":0.14}
    ts = tm.get(grade,800); a = am.get(size,36.6); k = km.get(cond,0.20)
    cf = 0.75*ts*a; dm = float(size.replace("M",""))/1000.0; nm = k*dm*cf
    return {"size":size,"grade":grade,"condition":cond,"nm":nm,"ftlb":nm*0.73756,"clamp_kn":cf/1000}

@app.get("/api/bulbs")
def bulbs(): return {"bulbs":BULBS}

@app.get("/api/batteries")
def batteries(): return {"batteries":BATTERIES}

@app.get("/api/tyres")
def tyres(): return {"tyres":TYRES}

@app.get("/api/wiring")
def wiring(): return {"circuits":WIRING}

@app.get("/api/obd-pids")
def obd_pids(): return {"pids":PIDS}

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
def list_jobs(): return {"jobs":db_list("jobs")}

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
        if "photos_after" in d: job["photos_after"] = d["photos_after"]
        db_save("jobs", jid, job)
    return {"success":True}

@app.delete("/api/jobs/{jid}")
def delete_job(jid: str): db_del("jobs",jid); return {"success":True}

# QUOTES
@app.get("/api/quotes")
def list_quotes(): return {"quotes":db_list("quotes")}

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

# APPOINTMENTS
@app.get("/api/appointments")
def list_appts(): return {"appointments":db_list("appointments")}

@app.post("/api/appointments")
async def create_appt(r: Request):
    d = await r.json(); aid = str(uuid.uuid4())[:6]
    row = {"id":aid,"customer":d.get("customer",""),"phone":d.get("phone",""),"vehicle":d.get("vehicle",""),"service":d.get("service",""),"date":d.get("date",""),"time":d.get("time",""),"created":now()}
    db_save("appointments",aid,row); return {"success":True,"appointment":row}

@app.delete("/api/appointments/{aid}")
def delete_appt(aid: str): db_del("appointments",aid); return {"success":True}

# CUSTOMERS
@app.get("/api/customers")
def list_cust(): return {"customers":db_list("customers")}

@app.post("/api/customers")
async def create_cust(r: Request):
    d = await r.json(); cid = str(uuid.uuid4())[:6]
    row = {"id":cid,"name":d.get("name",""),"phone":d.get("phone",""),"email":d.get("email",""),"created":today()}
    db_save("customers",cid,row); return {"success":True,"customer":row}

@app.delete("/api/customers/{cid}")
def delete_cust(cid: str): db_del("customers",cid); return {"success":True}

# INVOICES
@app.get("/api/invoices")
def list_inv(): return {"invoices":db_list("invoices")}

@app.post("/api/invoices")
async def create_inv(r: Request):
    d = await r.json(); labour = float(d.get("labour",0)); parts = float(d.get("parts",0))
    subtotal = labour+parts; vat = subtotal*0.15; total = subtotal+vat
    iid = str(uuid.uuid4())[:6]
    row = {"id":iid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),"description":d.get("description",""),"labour":labour,"parts":parts,"subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    db_save("invoices",iid,row); return {"success":True,"invoice":row}

@app.delete("/api/invoices/{iid}")
def delete_inv(iid: str): db_del("invoices",iid); return {"success":True}

# INVENTORY
@app.get("/api/inventory")
def list_inv_items(): return {"items":db_list("inventory")}

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

# STAFF
@app.get("/api/staff")
def list_staff(): return {"staff":db_list("staff")}

@app.post("/api/staff")
async def add_staff(r: Request):
    d = await r.json(); sid = str(uuid.uuid4())[:6]
    row = {"id":sid,"name":d.get("name",""),"role":d.get("role",""),"phone":d.get("phone",""),"email":d.get("email",""),"hourly_rate":float(d.get("hourly_rate",150)),"created":today()}
    db_save("staff",sid,row); return {"success":True,"staff":row}

@app.delete("/api/staff/{sid}")
def delete_staff(sid: str): db_del("staff",sid); return {"success":True}

# EXPENSES
@app.get("/api/expenses")
def list_exp(): return {"expenses":db_list("expenses")}

@app.post("/api/expenses")
async def add_exp(r: Request):
    d = await r.json(); eid = str(uuid.uuid4())[:6]
    row = {"id":eid,"category":d.get("category","Other"),"amount":float(d.get("amount",0)),"date":d.get("date",today()),"note":d.get("note",""),"created":now()}
    db_save("expenses",eid,row); return {"success":True,"expense":row}

@app.delete("/api/expenses/{eid}")
def delete_exp(eid: str): db_del("expenses",eid); return {"success":True}

# SUPPLIERS
@app.get("/api/suppliers")
def list_suppliers(): return {"suppliers":db_list("suppliers")}

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
