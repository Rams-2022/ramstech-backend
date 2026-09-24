from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

FAULT_CODES = {
    "P0101": {"code": "P0101", "description": "Mass Air Flow Circuit", "system": "Engine",
              "severity": "Medium", "is_electronic": True,
              "causes": ["Dirty MAF sensor", "Air leaks", "Clogged filter"],
              "symptoms": ["Poor economy", "Loss of power", "Rough idle"],
              "steps": ["Check filter", "Inspect intake", "Clean MAF"],
              "repairs": ["Clean/replace MAF", "Fix leaks"]},
    "P0300": {"code": "P0300", "description": "Multiple Cylinder Misfire", "system": "Engine",
              "severity": "High", "is_electronic": True,
              "causes": ["Faulty plugs", "Bad coils", "Fuel issues"],
              "symptoms": ["Engine shaking", "Loss of power"],
              "steps": ["Scan cylinders", "Check plugs", "Test coils"],
              "repairs": ["Replace plugs", "Replace coils"]},
    "P0401": {"code": "P0401", "description": "EGR Flow Insufficient", "system": "Engine",
              "severity": "Medium", "is_electronic": True,
              "causes": ["Clogged EGR", "Blocked passages"],
              "symptoms": ["Check engine light"],
              "steps": ["Inspect EGR", "Check passages"],
              "repairs": ["Clean EGR"]},
    "P0700": {"code": "P0700", "description": "Transmission Control System", "system": "Transmission",
              "severity": "High", "is_electronic": True,
              "causes": ["Internal fault", "TCM problem", "Solenoid failure"],
              "symptoms": ["Slipping", "Harsh shifting"],
              "steps": ["Scan TCM", "Check fluid"],
              "repairs": ["Replace solenoids", "Overhaul"]},
    "P0087": {"code": "P0087", "description": "Fuel Rail Pressure Too Low", "system": "Diesel Engine",
              "severity": "High", "is_electronic": True,
              "causes": ["Faulty HP pump", "Clogged filter", "Injector leak"],
              "symptoms": ["Won't start", "Loss of power"],
              "steps": ["Check pressure", "Inspect filter"],
              "repairs": ["Replace filter", "Replace pump"]},
    "P0234": {"code": "P0234", "description": "Turbo Overboost", "system": "Diesel Engine",
              "severity": "Medium", "is_electronic": True,
              "causes": ["Stuck wastegate", "Faulty sensor"],
              "symptoms": ["Loss of power", "Black smoke"],
              "steps": ["Check wastegate", "Test sensor"],
              "repairs": ["Free wastegate"]},
    "C0035": {"code": "C0035", "description": "LF Wheel Speed Sensor", "system": "ABS",
              "severity": "High", "is_electronic": True,
              "causes": ["Faulty sensor", "Damaged ring"],
              "symptoms": ["ABS light"],
              "steps": ["Check resistance", "Scope signal"],
              "repairs": ["Replace sensor"]},
    "HYD-001": {"code": "HYD-001", "description": "Low Hydraulic Pressure", "system": "Hydraulic",
                "severity": "High", "is_electronic": False,
                "causes": ["Worn pump", "Internal leaks", "Low fluid"],
                "symptoms": ["Slow operation", "Weak lifting"],
                "steps": ["Check fluid", "Test pressure"],
                "repairs": ["Replace pump", "Fix leaks"]},
    "PNEU-001": {"code": "PNEU-001", "description": "Air Compressor No Pressure", "system": "Pneumatic",
                 "severity": "High", "is_electronic": False,
                 "causes": ["Worn rings", "Leaking valves"],
                 "symptoms": ["Low pressure"],
                 "steps": ["Check belt", "Test output"],
                 "repairs": ["Replace compressor"]},
}


@router.get("/")
def list_codes(search: str = Query(None), system: str = Query(None),
               electronic: bool = Query(None)):
    results = list(FAULT_CODES.values())
    if search:
        q = search.lower()
        results = [c for c in results
                   if q in c["code"].lower() or q in c["description"].lower()
                   or q in c["system"].lower()]
    if system:
        results = [c for c in results if system.lower() in c["system"].lower()]
    if electronic is not None:
        results = [c for c in results if c["is_electronic"] == electronic]
    return {"count": len(results), "codes": results}


@router.get("/{code}")
def get_code(code: str):
    fc = FAULT_CODES.get(code.upper())
    if not fc:
        raise HTTPException(status_code=404, detail=f"Code {code} not found")
    return fc
