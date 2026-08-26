import time
import httpx
from apps.backend.src.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def run_performance_benchmarks():
    print("--- BENCHMARKING AEROMIND CLIMEGUARD API & LATENCY ---")
    
    # 1. Health endpoint latency
    latencies = []
    for _ in range(50):
        t0 = time.perf_counter()
        resp = client.get("/api/v1/health")
        dt = (time.perf_counter() - t0) * 1000.0
        latencies.append(dt)
    avg_health = sum(latencies) / len(latencies)
    p95_health = sorted(latencies)[int(len(latencies) * 0.95)]
    print(f"Health Check Latency: Avg = {avg_health:.2f} ms | P95 = {p95_health:.2f} ms")

    # 2. Telemetry & Locations query latency
    loc_latencies = []
    for _ in range(50):
        t0 = time.perf_counter()
        resp = client.get("/api/v1/locations")
        dt = (time.perf_counter() - t0) * 1000.0
        loc_latencies.append(dt)
    avg_loc = sum(loc_latencies) / len(loc_latencies)
    p95_loc = sorted(loc_latencies)[int(len(loc_latencies) * 0.95)]
    print(f"Locations Query Latency: Avg = {avg_loc:.2f} ms | P95 = {p95_loc:.2f} ms")

    # 3. Deterministic Risk Engine evaluation throughput
    from services.risk_engine.calculator import RiskEngine
    engine = RiskEngine()
    t0 = time.perf_counter()
    iterations = 5000
    for _ in range(iterations):
        engine.assess_risk("LOC-1", 38.5, 24.0, 3.2, 0.6, [{"type": "FIRE_DETECTED", "confidence": 0.9}], people_in_danger_zone=1)
    total_time = time.perf_counter() - t0
    ops_per_sec = iterations / total_time
    print(f"Risk Engine Throughput: {ops_per_sec:.0f} assessments/sec ({total_time*1000/iterations:.3f} ms per assessment)")

    # 4. Statistical Anomaly Detector throughput
    from services.analytics.anomaly import AnomalyDetector
    detector = AnomalyDetector()
    t0 = time.perf_counter()
    for i in range(iterations):
        detector.update_and_detect("LOC-1", "temp", 24.0 + (i % 10))
    total_time = time.perf_counter() - t0
    anomaly_ops = iterations / total_time
    print(f"Anomaly Detector Throughput: {anomaly_ops:.0f} updates/sec ({total_time*1000/iterations:.3f} ms per update)")

if __name__ == "__main__":
    run_performance_benchmarks()
