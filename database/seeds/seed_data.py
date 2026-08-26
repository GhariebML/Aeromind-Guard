import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from database.models import (
    Organization, User, Location, Camera, DataSource,
    TemperatureReading, EnvironmentalReading, RiskScore,
    Alert, AIDecision, ModelVersion
)

def seed_database(db: Session):
    """
    Populates database with realistic physical facility structures, cameras, and baseline telemetry.
    """
    # 1. Organization
    org = db.query(Organization).filter_by(name="AeroMind Industrial Operations").first()
    if not org:
        org = Organization(
            id=str(uuid.uuid4()),
            name="AeroMind Industrial Operations"
        )
        db.add(org)
        db.flush()

    # 2. User
    user = db.query(User).filter_by(email="operator@aeromind.io").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            email="operator@aeromind.io",
            full_name="Lead Safety Officer",
            role="OPERATOR",
            is_active=True
        )
        db.add(user)

    # 3. Monitored Locations / Zones
    zones_data = [
        {
            "name": "Battery Energy Storage System (BESS) - Sector 1",
            "code": "ZONE-BESS-01",
            "zone_type": "INDUSTRIAL",
            "latitude": 24.4539,
            "longitude": 54.3773,
            "elevation_m": 12.0,
            "baseline_temp_c": 26.5,
            "risk_threshold": 65.0,
            "metadata_json": {"building": "Substation B", "hazardous_materials": "Lithium-ion Cells"}
        },
        {
            "name": "Solar Array Inverter Field - Sector 4",
            "code": "ZONE-SOLAR-04",
            "zone_type": "PERIMETER",
            "latitude": 24.4552,
            "longitude": 54.3791,
            "elevation_m": 15.0,
            "baseline_temp_c": 32.0,
            "risk_threshold": 75.0,
            "metadata_json": {"capacity_mw": 50, "inverters_count": 24}
        },
        {
            "name": "Central Refining & Thermal Cracker Yard",
            "code": "ZONE-REFINERY-02",
            "zone_type": "INDUSTRIAL",
            "latitude": 24.4518,
            "longitude": 54.3755,
            "elevation_m": 8.0,
            "baseline_temp_c": 34.0,
            "risk_threshold": 70.0,
            "metadata_json": {"high_pressure_lines": True, "flaring_unit": True}
        },
        {
            "name": "Rooftop Cooling Towers & HVAC Complex",
            "code": "ZONE-ROOFTOP-09",
            "zone_type": "ROOFTOP",
            "latitude": 24.4560,
            "longitude": 54.3740,
            "elevation_m": 42.0,
            "baseline_temp_c": 28.0,
            "risk_threshold": 60.0,
            "metadata_json": {"chillers_count": 8, "coolant_type": "R134a"}
        }
    ]

    locations = []
    for z in zones_data:
        loc = db.query(Location).filter_by(code=z["code"]).first()
        if not loc:
            loc = Location(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                name=z["name"],
                code=z["code"],
                zone_type=z["zone_type"],
                latitude=z["latitude"],
                longitude=z["longitude"],
                elevation_m=z["elevation_m"],
                baseline_temp_c=z["baseline_temp_c"],
                risk_threshold=z["risk_threshold"],
                is_active=True,
                metadata_json=z["metadata_json"]
            )
            db.add(loc)
            db.flush()
        locations.append(loc)

    # 4. Cameras
    cameras_data = [
        {
            "location_id": locations[0].id,
            "name": "BESS Thermal Optical Cam 01",
            "code": "CAM-BESS-01",
            "camera_type": "THERMAL",
            "danger_zones": [{"polygon": [[100, 100], [400, 100], [400, 350], [100, 350]], "name": "BESS Battery Rack 1-4"}]
        },
        {
            "location_id": locations[1].id,
            "name": "Solar Yard Perimeter Cam 04",
            "code": "CAM-SOLAR-04",
            "camera_type": "CCTV_OPTICAL",
            "danger_zones": [{"polygon": [[150, 120], [500, 120], [500, 400], [150, 400]], "name": "High Voltage Transformer"}]
        },
        {
            "location_id": locations[2].id,
            "name": "Cracker Flange PTZ Cam 02",
            "code": "CAM-REFINERY-02",
            "camera_type": "CCTV_OPTICAL",
            "danger_zones": [{"polygon": [[80, 80], [450, 80], [450, 420], [80, 420]], "name": "Hydrocarbon Flange Enclosure"}]
        },
        {
            "location_id": locations[3].id,
            "name": "Rooftop Drone Overwatch 09",
            "code": "CAM-UAV-09",
            "camera_type": "DRONE_UAV",
            "danger_zones": []
        }
    ]

    for c in cameras_data:
        cam = db.query(Camera).filter_by(code=c["code"]).first()
        if not cam:
            cam = Camera(
                id=str(uuid.uuid4()),
                location_id=c["location_id"],
                name=c["name"],
                code=c["code"],
                camera_type=c["camera_type"],
                status="ONLINE",
                fps=30.0,
                resolution="1920x1080",
                danger_zones=c["danger_zones"],
                is_active=True
            )
            db.add(cam)

    # 5. Data Sources
    for loc in locations:
        ds = db.query(DataSource).filter_by(location_id=loc.id).first()
        if not ds:
            db.add(DataSource(
                id=str(uuid.uuid4()),
                location_id=loc.id,
                name=f"{loc.name} Ingestion Gateway",
                provider="FORTYGUARD",
                source_type="WEATHER_API",
                status="ACTIVE",
                is_demo=False
            ))

    # 6. Model Versions
    models_meta = [
        {"name": "YOLOv8m-Physical-AI", "task": "DETECTION", "version": "v1.4.0", "model_path": "models/detection/yolov8m.pt"},
        {"name": "BoT-SORT-Tracker", "task": "TRACKING", "version": "v2.1.0", "model_path": "models/tracking/botsort.yaml"},
        {"name": "AeroMind-ZScore-RoC", "task": "ANOMALY", "version": "v1.0.0", "model_path": "services/analytics/anomaly.py"},
        {"name": "Deterministic-Risk-Engine", "task": "RISK", "version": "v3.0.0", "model_path": "services/risk_engine/calculator.py"}
    ]
    for m in models_meta:
        if not db.query(ModelVersion).filter_by(name=m["name"]).first():
            db.add(ModelVersion(
                id=str(uuid.uuid4()),
                name=m["name"],
                task=m["task"],
                version=m["version"],
                model_path=m["model_path"],
                is_active=True
            ))

    # 7. Initial baseline telemetry
    now = datetime.now(timezone.utc)
    for loc in locations:
        # 12 historical points for charts
        for h in range(12, 0, -1):
            t_stamp = now - timedelta(hours=h)
            temp = loc.baseline_temp_c + (2.0 if h % 2 == 0 else -1.0)
            db.add(TemperatureReading(
                id=str(uuid.uuid4()),
                location_id=loc.id,
                timestamp=t_stamp,
                ambient_temp_c=temp,
                surface_temp_c=temp + 3.0,
                rate_of_change_c_per_hr=0.2,
                is_anomaly=False,
                anomaly_score=0.05,
                source_provider="FORTYGUARD"
            ))
            db.add(EnvironmentalReading(
                id=str(uuid.uuid4()),
                location_id=loc.id,
                timestamp=t_stamp,
                metric="humidity",
                value=55.0 - (temp - 25.0) * 1.5,
                unit="%",
                quality=1.0,
                is_anomaly=False
            ))

        # Initial Risk Score
        db.add(RiskScore(
            id=str(uuid.uuid4()),
            location_id=loc.id,
            timestamp=now,
            overall_score=18.5,
            severity="LOW",
            factors_json=[
                {"name": "Temperature Elevation", "category": "ENVIRONMENTAL", "score_contribution": 8.0, "weight": 1.0, "description": "Nominal baseline tracking"},
                {"name": "Baseline Volatility", "category": "TEMPORAL", "score_contribution": 10.5, "weight": 1.0, "description": "Standard diurnal fluctuation"}
            ],
            calculation_breakdown="Overall Risk Score: 18.5 (LOW)\n- Temperature Elevation: +8.0\n- Baseline Volatility: +10.5"
        ))

    db.commit()
