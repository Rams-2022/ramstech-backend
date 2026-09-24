from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

PARTS = {
    "04152-YZZA1": {"part_number": "04152-YZZA1", "name": "Oil Filter", "category": "Engine",
                    "description": "High-efficiency oil filter", "price": 15.00, "currency": "ZAR",
                    "compatible_vehicles": ["Toyota Hilux", "Fortuner"], "manufacturer": "Toyota"},
    "17801-30060": {"part_number": "17801-30060", "name": "Air Filter", "category": "Engine",
                    "description": "Engine air filter element", "price": 25.00, "currency": "ZAR",
                    "compatible_vehicles": ["Toyota Hilux"], "manufacturer": "Toyota"},
    "04465-YZZE8": {"part_number": "04465-YZZE8", "name": "Brake Pads Front", "category": "Brakes",
                    "description": "Front brake pad set", "price": 55.00, "currency": "ZAR",
                    "compatible_vehicles": ["Toyota Hilux"], "manufacturer": "Toyota"},
    "23390-30020": {"part_number": "23390-30020", "name": "Fuel Filter", "category": "Fuel System",
                    "description": "Diesel fuel filter", "price": 35.00, "currency": "ZAR",
                    "compatible_vehicles": ["Toyota Hilux Diesel"], "manufacturer": "Toyota"},
}


@router.get("/")
def search_parts(q: str = Query("")):
    if not q:
        return {"count": len(PARTS), "parts": list(PARTS.values())}
    lq = q.lower()
    results = [p for p in PARTS.values()
               if lq in p["part_number"].lower() or lq in p["name"].lower()
               or any(lq in v.lower() for v in p["compatible_vehicles"])]
    return {"count": len(results), "parts": results}


@router.get("/{part_number}")
def get_part(part_number: str):
    clean = part_number.replace("-", "").replace(" ", "").upper()
    for pn, p in PARTS.items():
        if pn.replace("-", "") == clean or clean in pn.replace("-", ""):
            return p
    raise HTTPException(status_code=404, detail=f"Part {part_number} not found")
