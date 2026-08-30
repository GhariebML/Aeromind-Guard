import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import jwt

# Need to set env variables before imports
os.environ["APP_MODE"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-123"

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

def test_login_success():
    response = client.post("/api/v1/auth/login", data={"username": "admin@aeromind.io", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["role"] == "admin"

def test_login_failure():
    response = client.post("/api/v1/auth/login", data={"username": "admin@aeromind.io", "password": "wrongpassword"})
    assert response.status_code == 401

def test_protected_route_without_token():
    response = client.get("/api/v1/system/status")
    assert response.status_code == 401

def test_protected_route_with_valid_token():
    # Login first
    login = client.post("/api/v1/auth/login", data={"username": "operator@aeromind.io", "password": "operator123"})
    token = login.json()["access_token"]
    
    # Access route
    response = client.get("/api/v1/system/status", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["status"] in ["HEALTHY", "DEGRADED"]

def test_invalid_jwt_token():
    response = client.get("/api/v1/system/status", headers={"Authorization": "Bearer invalid.token.string"})
    assert response.status_code == 401

def test_websocket_without_token():
    with pytest.raises(Exception) as excinfo:
        with client.websocket_connect("/ws") as websocket:
            pass
    assert "403" in str(excinfo.value) or "1008" in str(excinfo.value)

def test_websocket_with_invalid_token():
    with pytest.raises(Exception) as excinfo:
        with client.websocket_connect("/ws?token=badtoken") as websocket:
            pass
    assert "403" in str(excinfo.value) or "1008" in str(excinfo.value)

def test_websocket_with_valid_token():
    login = client.post("/api/v1/auth/login", data={"username": "operator@aeromind.io", "password": "operator123"})
    token = login.json()["access_token"]
    
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert "pong" in data
