import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def student_token(client):
    r = client.post("/api/auth/login", json={"email": "student@quickbite.demo", "password": "Student@123"})
    assert r.status_code == 200, f"Failed student login: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def staff_token(client):
    r = client.post("/api/auth/login", json={"email": "staff@quickbite.demo", "password": "Staff@123"})
    assert r.status_code == 200, f"Failed staff login: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post("/api/auth/login", json={"email": "admin@quickbite.demo", "password": "Admin@123"})
    assert r.status_code == 200, f"Failed admin login: {r.text}"
    return r.json()["access_token"]
