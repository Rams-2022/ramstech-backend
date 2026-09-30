# app/data.py — Static reference data
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
     "co":["ECU → MAF: signal+ground+power","ECU → MAP: signal+ground+5V","ECU → TPS: 5V+signal+ground"],
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
     "co":["TCM → Sol A (Red)","TCM → Sol B (Blue)","TCM → Line pressure (Yellow)"],
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
