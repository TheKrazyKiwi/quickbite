from uuid import uuid4


def test_login_success(client):
    r = client.post("/api/auth/login", json={"email": "student@quickbite.demo", "password": "Student@123"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == "student@quickbite.demo"
    assert data["user"]["role"] == "STUDENT"


def test_login_invalid_password(client):
    r = client.post("/api/auth/login", json={"email": "student@quickbite.demo", "password": "WrongPassword"})
    assert r.status_code == 401


def test_register_student_success(client):
    unique_email = f"test_{uuid4().hex[:8]}@quickbite.demo"
    r = client.post("/api/auth/register", json={
        "name": "Test Student",
        "email": unique_email,
        "password": "Password@123",
        "phone": "9876543210",
        "department": "Information Science"
    })
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["role"] == "STUDENT"


def test_register_duplicate_email(client):
    r = client.post("/api/auth/register", json={
        "name": "Duplicate Student",
        "email": "student@quickbite.demo",
        "password": "Password@123"
    })
    assert r.status_code == 409


def test_auth_me(client, student_token):
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "student@quickbite.demo"
