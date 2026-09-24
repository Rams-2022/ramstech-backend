from fastapi import APIRouter, HTTPException

router = APIRouter()

WMI = {
    "1HG": ("Honda", "USA"), "1FT": ("Ford", "USA"), "1GC": ("Chevrolet", "USA"),
    "4T1": ("Toyota", "USA"), "5YJ": ("Tesla", "USA"),
    "JHM": ("Honda", "Japan"), "JTD": ("Toyota", "Japan"), "JTM": ("Toyota", "Japan"),
    "KMH": ("Hyundai", "Korea"), "KNA": ("Kia", "Korea"),
    "SAL": ("Land Rover", "UK"), "SAJ": ("Jaguar", "UK"),
    "WBA": ("BMW", "Germany"), "WDB": ("Mercedes-Benz", "Germany"),
    "WVW": ("Volkswagen", "Germany"), "YV1": ("Volvo", "Sweden"),
    "ZFA": ("Fiat", "Italy"), "ZFF": ("Ferrari", "Italy"),
    "AAV": ("VW South Africa", "South Africa"), "AHT": ("Toyota SA", "South Africa"),
    "AFA": ("Ford SA", "South Africa"), "ADB": ("Mercedes SA", "South Africa"),
}

YEAR_CODES = {
    "A": 2010, "B": 2011, "C": 2012, "D": 2013, "E": 2014,
    "F": 2015, "G": 2016, "H": 2017, "J": 2018, "K": 2019,
    "L": 2020, "M": 2021, "N": 2022, "P": 2023, "R": 2024,
    "Y": 2000, "1": 2001, "2": 2002, "3": 2003, "4": 2004,
    "5": 2005, "6": 2006, "7": 2007, "8": 2008, "9": 2009,
}

VEHICLE_TYPE = {
    "A": "Passenger Car", "B": "Passenger Car", "C": "Passenger Car",
    "D": "Passenger Car", "E": "Passenger Car", "J": "SUV",
    "K": "SUV", "L": "SUV", "M": "MPV", "N": "Pickup",
    "P": "Commercial", "T": "Truck", "U": "Bus", "V": "Van",
    "Y": "Motorcycle", "W": "Trailer",
}

REGION = {
    "1": "North America", "2": "North America", "4": "North America", "5": "North America",
    "J": "Asia", "K": "Asia", "L": "Asia", "M": "Asia", "P": "Asia",
    "S": "Europe", "T": "Europe", "V": "Europe", "W": "Europe", "X": "Europe",
    "Y": "Europe", "Z": "Europe",
    "A": "Africa", "B": "Africa", "C": "Africa", "D": "Africa",
}


@router.get("/{vin}")
def decode_vin(vin: str):
    v = vin.strip().upper()
    if len(v) != 17:
        raise HTTPException(status_code=400, detail="VIN must be 17 characters")
    if any(c in v for c in "IOQ"):
        raise HTTPException(status_code=400, detail="VIN cannot contain I, O, or Q")

    wmi = v[:3]
    manufacturer, country = WMI.get(wmi, ("Unknown", "Unknown"))
    year = YEAR_CODES.get(v[9], "Unknown")
    body = VEHICLE_TYPE.get(v[3], "Unknown")
    region = REGION.get(v[0], "Unknown")

    return {
        "vin": v,
        "valid": True,
        "manufacturer": manufacturer,
        "country": country,
        "region": region,
        "year": year,
        "body_type": body,
        "wmi": wmi,
        "serial_number": v[10:],
    }
