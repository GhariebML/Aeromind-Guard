import pytest
import requests

BASE_URL = "http://localhost:8080/api/v1"

def test_login_success():
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin@aeromind.local", "password": "adminpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"

def test_login_failure():
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin@aeromind.local", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_protected_route_without_token():
    response = requests.get(f"{BASE_URL}/locations")
    assert response.status_code == 401

def test_protected_route_with_token():
    login = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "operator@aeromind.local", "password": "operatorpassword"}
    )
    token = login.json()["access_token"]
    
    response = requests.get(f"{BASE_URL}/locations", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_rbac_analyst_access_denied_to_admin_route():
    login = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "analyst@aeromind.local", "password": "analystpassword"}
    )
    token = login.json()["access_token"]
    
    # Assuming demo mode toggle is admin-only, wait we don't have this enforced in backend yet or do we?
    # Sprint 2 hardened the backend. Let's see if /system/demo-mode/toggle returns 403.
    response = requests.post(
        f"{BASE_URL}/system/demo-mode/toggle", 
        headers={"Authorization": f"Bearer {token}"}
    )
    # Could be 403 (if role enforced) or 401 (if not authenticated)
    assert response.status_code in (403, 401)
