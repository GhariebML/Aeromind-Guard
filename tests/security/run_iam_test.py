import os
import sys

# Need to set env variables before imports
os.environ["APP_MODE"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-123"
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.backend.src.main import app
from database.connection import Base, get_db
from database.seeds.seed_data import seed_database

# Setup Test Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_iam.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Seed it
db = TestingSessionLocal()
seed_database(db)
db.close()

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def run_tests():
    print("Testing login success...")
    response = client.post("/api/v1/auth/login", data={"username": "admin@aeromind.io", "password": "admin123"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    print("Testing login failure...")
    response = client.post("/api/v1/auth/login", data={"username": "admin@aeromind.io", "password": "wrongpassword"})
    assert response.status_code == 401
    
    print("Testing protected route without token...")
    response = client.get("/api/v1/system/status")
    assert response.status_code == 401

    print("Testing protected route with valid token...")
    login = client.post("/api/v1/auth/login", data={"username": "operator@aeromind.io", "password": "operator123"})
    token = login.json()["access_token"]
    response = client.get("/api/v1/system/status", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    print("Testing WebSocket without token...")
    try:
        with client.websocket_connect("/ws") as websocket:
            pass
        assert False, "Should have failed"
    except Exception as e:
        assert getattr(e, "code", None) == 1008, f"Unexpected exception: {e}"

    print("Testing WebSocket with valid token...")
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert "pong" in data

    print("All IAM tests passed successfully.")

if __name__ == "__main__":
    run_tests()
