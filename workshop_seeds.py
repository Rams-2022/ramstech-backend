"""Seed data for the workshop assistant. Run once from Render shell:
    python -c 'import workshop_seed; workshop_seed.seed_dtc()'
    python -c 'import workshop_seed; workshop_seed.seed_procedures()'
"""
import db

DTC_SEED = [
    # (code, description, category, severity, is_generic, [repairs])
    ("P0100", "Mass Air Flow Circuit Malfunction", "powertrain", "medium", True, [
        (1, "Clean or replace MAF sensor", "Easy DIY", 250, 1800, 1.0,
         "1. Inspect MAF sensor wiring for damage.\n2. Clean MAF with MAF cleaner spray.\n3. Reset codes and test drive.\n4. Replace MAF if fault returns."),
        (2, "Check for vacuum leaks", "Moderate DIY", 50, 400, 0.5,
         "1. Inspect intake hoses for cracks.\n2. Spray carb cleaner around intake, listen for idle change.\n3. Replace cracked hoses."),
    ]),
    ("P0101", "Mass Air Flow Circuit Range/Performance", "powertrain", "medium", True, [
        (1, "Replace air filter and clean MAF", "Easy DIY", 150, 1200, 0.5,
         "1. Replace air filter.\n2. Clean MAF sensor.\n3. Clear codes and test."),
    ]),
    ("P0110", "Intake Air Temperature Circuit Malfunction", "powertrain", "low", True, [
        (1, "Replace IAT sensor", "Easy DIY", 200, 800, 0.5,
         "1. Locate IAT sensor (usually on intake tube).\n2. Disconnect, test resistance.\n3. Replace if out of spec."),
    ]),
    ("P0115", "Engine Coolant Temperature Circuit Malfunction", "powertrain", "medium", True, [
        (1, "Replace coolant temp sensor", "Moderate DIY", 250, 1200, 1.0,
         "1. Allow engine to cool fully.\n2. Drain coolant.\n3. Replace ECT sensor.\n4. Refill and bleed cooling system."),
    ]),
    ("P0120", "Throttle Position Sensor Circuit Malfunction", "powertrain", "medium", True, [
        (1, "Replace TPS", "Moderate DIY", 400, 2500, 1.0,
         "1. Disconnect TPS connector.\n2. Test resistance across range.\n3. Replace TPS, reset adaptation."),
    ]),
    ("P0130", "O2 Sensor Circuit Malfunction (Bank 1, Sensor 1)", "powertrain", "medium", True, [
        (1, "Replace upstream O2 sensor", "Moderate DIY", 800, 3500, 1.5,
         "1. Warm engine to operating temp.\n2. Disconnect O2 sensor.\n3. Remove with O2 socket.\n4. Install new sensor with anti-seize.\n5. Clear codes."),
    ]),
    ("P0135", "O2 Sensor Heater Circuit Malfunction (Bank 1, Sensor 1)", "powertrain", "low", True, [
        (1, "Replace O2 sensor (heater failed)", "Moderate DIY", 800, 3500, 1.5,
         "1. Check O2 heater fuse first.\n2. If fuse OK, replace sensor."),
    ]),
    ("P0171", "System Too Lean (Bank 1)", "powertrain", "medium", True, [
        (1, "Check for vacuum leaks", "Easy DIY", 0, 500, 0.5,
         "1. Inspect all intake hoses and gaskets.\n2. Spray carb cleaner around intake.\n3. Replace cracked hoses."),
        (2, "Clean MAF sensor", "Easy DIY", 100, 300, 0.5,
         "1. Remove MAF.\n2. Spray with MAF cleaner.\n3. Reinstall and test."),
        (3, "Check fuel pressure", "Professional", 0, 500, 1.0,
         "1. Connect fuel pressure gauge.\n2. Compare to spec.\n3. Replace pump/filter if low."),
    ]),
    ("P0174", "System Too Lean (Bank 2)", "powertrain", "medium", True, [
        (1, "Check for vacuum leaks", "Easy DIY", 0, 500, 0.5,
         "1. Inspect intake hoses.\n2. Check intake manifold gaskets."),
    ]),
    ("P0300", "Random/Multiple Cylinder Misfire Detected", "powertrain", "high", True, [
        (1, "Replace spark plugs and check coils", "Moderate DIY", 600, 4000, 1.5,
         "1. Read misfire counters per cylinder.\n2. Inspect spark plugs.\n3. Swap coils between cylinders to isolate.\n4. Replace faulty coil(s) and all plugs."),
        (2, "Check fuel injectors", "Professional", 1200, 8000, 3.0,
         "1. Test injector resistance.\n2. Perform injector balance test.\n3. Replace faulty injectors."),
    ]),
    ("P0301", "Cylinder 1 Misfire Detected", "powertrain", "high", True, [
        (1, "Swap coil to another cylinder to isolate", "Easy DIY", 0, 0, 0.5,
         "1. Note misfire on cyl 1.\n2. Swap coil 1 with coil 2.\n3. Clear codes, drive.\n4. If misfire moves to cyl 2, replace coil."),
        (2, "Replace spark plug cyl 1", "Easy DIY", 150, 500, 0.5,
         "1. Remove spark plug.\n2. Inspect for fouling/wear.\n3. Replace with correct gap."),
    ]),
    ("P0302", "Cylinder 2 Misfire Detected", "powertrain", "high", True, []),
    ("P0303", "Cylinder 3 Misfire Detected", "powertrain", "high", True, []),
    ("P0304", "Cylinder 4 Misfire Detected", "powertrain", "high", True, []),
    ("P0401", "EGR Flow Insufficient", "powertrain", "medium", True, [
        (1, "Clean EGR valve and passages", "Moderate DIY", 100, 800, 2.0,
         "1. Remove EGR valve.\n2. Clean with carb cleaner.\n3. Clear carbon from intake passages.\n4. Reinstall with new gasket."),
    ]),
    ("P0420", "Catalyst System Efficiency Below Threshold (Bank 1)", "powertrain", "medium", True, [
        (1, "Replace downstream O2 sensor", "Moderate DIY", 800, 3500, 1.5,
         "1. Test downstream O2 sensor signal.\n2. Replace if sluggish."),
        (2, "Replace catalytic converter", "Professional", 3500, 15000, 3.0,
         "1. Confirm cat is genuinely failed (not sensor).\n2. Replace with OEM or approved aftermarket."),
    ]),
    ("P0440", "Evaporative Emission System Malfunction", "powertrain", "low", True, [
        (1, "Tighten or replace fuel cap", "Easy DIY", 100, 400, 0.1,
         "1. Tighten fuel cap until click.\n2. Clear codes.\n3. If returns, replace cap."),
    ]),
    ("P0442", "EVAP System Small Leak Detected", "powertrain", "low", True, [
        (1, "Smoke test EVAP system", "Professional", 400, 1500, 1.5,
         "1. Perform smoke test.\n2. Locate leak.\n3. Replace leaking hose/valve."),
    ]),
    ("P0455", "EVAP System Large Leak Detected", "powertrain", "low", True, [
        (1, "Check fuel cap and EVAP hoses", "Easy DIY", 100, 800, 0.5,
         "1. Inspect fuel cap seal.\n2. Inspect charcoal canister hoses."),
    ]),
    ("P0500", "Vehicle Speed Sensor Malfunction", "powertrain", "medium", True, [
        (1, "Replace VSS", "Moderate DIY", 400, 2000, 1.0,
         "1. Locate VSS on transmission.\n2. Disconnect connector.\n3. Remove sensor.\n4. Replace and clear codes."),
    ]),
    ("P0505", "Idle Control System Malfunction", "powertrain", "medium", True, [
        (1, "Clean idle air control valve", "Moderate DIY", 100, 600, 1.0,
         "1. Remove IAC valve.\n2. Clean with throttle body cleaner.\n3. Reinstall with new gasket."),
    ]),
    ("P0562", "System Voltage Low", "powertrain", "medium", True, [
        (1, "Test battery and alternator", "Easy DIY", 0, 3500, 0.5,
         "1. Measure battery voltage (12.6V engine off).\n2. Measure charging voltage (13.8–14.4V running).\n3. Replace battery or alternator as needed."),
    ]),
    ("P0600", "Serial Communication Link Malfunction", "powertrain", "high", True, []),
    ("P0700", "Transmission Control System Malfunction", "powertrain", "high", True, [
        (1, "Scan TCM for specific codes", "Professional", 0, 0, 0.5,
         "1. Use transmission-capable scanner.\n2. Read TCM-specific codes.\n3. Diagnose based on those codes."),
    ]),
    ("P0705", "Transmission Range Sensor Circuit Malfunction", "powertrain", "medium", True, []),
    ("P0740", "Torque Converter Clutch Circuit Malfunction", "powertrain", "high", True, []),
    ("P0750", "Shift Solenoid A Malfunction", "powertrain", "high", True, []),
    ("P0171", "System Too Lean (Bank 1)", "powertrain", "medium", True, []),
    ("B0001", "Driver Frontal Stage 1 Deployment Control", "body", "high", False, []),
    ("B1000", "ECU Internal Malfunction", "body", "high", False, []),
    ("B1318", "Battery Voltage Low", "body", "medium", False, [
        (1, "Test battery and charging system", "Easy DIY", 0, 3500, 0.5,
         "1. Load test battery.\n2. Test alternator output."),
    ]),
    ("B1342", "ECU is Faulted", "body", "high", False, [
        (1, "Replace or reprogram module", "Professional", 2500, 12000, 2.0,
         "1. Confirm module fault.\n2. Replace or reflash module.\n3. Program to vehicle."),
    ]),
    ("C0035", "Left Front Wheel Speed Sensor Circuit", "chassis", "medium", True, [
        (1, "Replace wheel speed sensor", "Moderate DIY", 400, 2000, 1.0,
         "1. Inspect sensor wiring.\n2. Test sensor resistance.\n3. Replace if open/short."),
    ]),
    ("C0040", "Right Front Wheel Speed Sensor Circuit", "chassis", "medium", True, []),
    ("C0050", "Right Rear Wheel Speed Sensor Circuit", "chassis", "medium", True, []),
    ("C0110", "Pump Motor Circuit Malfunction (ABS)", "chassis", "high", True, []),
    ("U0100", "Lost Communication With ECM/PCM", "network", "high", True, [
        (1, "Check CAN bus wiring", "Professional", 0, 3000, 2.0,
         "1. Check CAN H and CAN L for opens/shorts.\n2. Check terminating resistors.\n3. Repair wiring."),
    ]),
    ("U0101", "Lost Communication With TCM", "network", "high", True, []),
    ("U0121", "Lost Communication With ABS Module", "network", "high", True, []),
    ("U0155", "Lost Communication With Instrument Panel Cluster", "network", "medium", True, []),
    # Add more rows as needed. Truncated here for brevity.
]


def seed_dtc():
    """Insert DTC seed data. Idempotent — skips existing codes."""
    if not db.is_ready():
        print("[seed] Database not configured")
        return {"error": "db not ready"}

    c = db._client()
    inserted_codes = 0
    inserted_repairs = 0

    for row in DTC_SEED:
        code, desc, cat, sev, generic, repairs = row
        existing = c.table("dtc_codes").select("code").eq("code", code).execute()
        if not existing.data:
            c.table("dtc_codes").insert({
                "code": code, "description": desc, "category": cat,
                "severity": sev, "is_generic": generic,
            }).execute()
            inserted_codes += 1

        for rep in repairs:
            rank, title, skill, cmin, cmax, hours, steps = rep
            c.table("dtc_repairs").insert({
                "code": code, "likelihood_rank": rank, "title": title,
                "skill_level": skill, "parts_cost_min": cmin,
                "parts_cost_max": cmax, "labor_hours": hours, "steps": steps,
            }).execute()
            inserted_repairs += 1

    print(f"[seed] Inserted {inserted_codes} codes, {inserted_repairs} repairs")
    return {"codes": inserted_codes, "repairs": inserted_repairs}


PROCEDURE_SEED = [
    {
        "vehicle_make": "Toyota", "vehicle_model": "Hilux",
        "year_from": 2005, "year_to": 2020, "system": "engine",
        "title": "Diesel Injector Replacement – Toyota Hilux 2.5 D-4D",
        "safety_level": "high",
        "tools_required": "14mm spanner, torque wrench, injector puller, new copper washers, thread sealant",
        "torque_specs": "Injector clamp bolts: 22 Nm. Fuel line unions: 30 Nm.",
        "content": (
            "SAFETY: Diesel fuel is flammable and under high pressure. Wear safety glasses "
            "and nitrile gloves. Depressurise the fuel system before opening any line.\n\n"
            "1. Disconnect battery negative terminal.\n"
            "2. Remove engine cover (10mm bolts).\n"
            "3. Disconnect injector electrical connectors.\n"
            "4. Depressurise fuel system by loosening the fuel filter outlet union.\n"
            "5. Remove fuel return line from each injector (17mm).\n"
            "6. Remove injector clamp bolts (14mm).\n"
            "7. Use injector puller to extract injectors.\n"
            "8. Remove and discard copper washers.\n"
            "9. Clean injector seats with a soft brush.\n"
            "10. Install new copper washers and injectors.\n"
            "11. Torque clamp bolts to 22 Nm.\n"
            "12. Reconnect fuel lines to 30 Nm.\n"
            "13. Reconnect electrical connectors.\n"
            "14. Crank engine without starting (disable fuel pump) to prime.\n"
            "15. Start engine, check for leaks, clear DTCs."
        ),
    },
    {
        "vehicle_make": "Ford", "vehicle_model": "Ranger",
        "year_from": 2012, "year_to": 2022, "system": "engine",
        "title": "Cambelt / Timing Belt Replacement – Ford Ranger 2.2 TDCi",
        "safety_level": "high",
        "tools_required": "Cam locking tool, crank locking pin, torque wrench, socket set, new belt kit",
        "torque_specs": "Crank pulley bolt: 120 Nm + 90°. Tensioner: 25 Nm.",
        "content": (
            "SAFETY: Engine must be cold. Do not turn crank with belt removed on some models.\n\n"
            "1. Disconnect battery negative.\n"
            "2. Remove auxiliary belt and pulleys.\n"
            "3. Remove timing cover.\n"
            "4. Rotate engine to TDC using crank bolt.\n"
            "5. Lock cam with cam locking tool and crank with locking pin.\n"
            "6. Mark belt direction of rotation.\n"
            "7. Loosen tensioner and remove belt.\n"
            "8. Replace tensioner and idler pulleys.\n"
            "9. Install new belt following manufacturer marks.\n"
            "10. Tension belt, remove locking tools.\n"
            "11. Rotate engine two full turns by hand, verify timing marks align.\n"
            "12. Reinstall timing cover, aux belt.\n"
            "13. Start engine, verify no unusual noise."
        ),
    },
    {
        "vehicle_make": "Volkswagen", "vehicle_model": "Polo",
        "year_from": 2010, "year_to": 2020, "system": "electrical",
        "title": "Alternator Replacement – VW Polo 1.4",
        "safety_level": "medium",
        "tools_required": "13mm spanner, 16mm spanner, torque wrench, multimeter",
        "torque_specs": "Alternator mounting bolts: 25 Nm. B+ terminal: 15 Nm.",
        "content": (
            "SAFETY: Disconnect battery negative before touching alternator.\n\n"
            "1. Disconnect battery negative terminal.\n"
            "2. Remove serpentine belt (release tensioner).\n"
            "3. Disconnect B+ cable from alternator.\n"
            "4. Disconnect alternator electrical connector.\n"
            "5. Remove mounting bolts.\n"
            "6. Extract alternator.\n"
            "7. Install new alternator in reverse order.\n"
            "8. Torque mounting bolts to 25 Nm.\n"
            "9. Reinstall belt.\n"
            "10. Reconnect battery, start engine, verify charging voltage 13.8–14.4V."
        ),
    },
]


def seed_procedures():
    """Insert sample procedures and generate their embeddings."""
    if not db.is_ready():
        print("[seed] Database not configured")
        return {"error": "db not ready"}

    import workshop_ai
    c = db._client()
    inserted = 0

    for p in PROCEDURE_SEED:
        existing = c.table("procedures").select("id")\
            .eq("title", p["title"]).execute()
        if existing.data:
            continue
        try:
            p["embedding"] = workshop_ai.embed(p["content"])
        except Exception as e:
            print(f"[seed] Embed failed for {p['title']}: {e}")
            continue
        c.table("procedures").insert(p).execute()
        inserted += 1

    print(f"[seed] Inserted {inserted} procedures")
    return {"procedures": inserted}
