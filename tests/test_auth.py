# tests/test_auth.py
from urllib import response

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import User, Client
from app.utils.security import hash_password

client = TestClient(app)

# Test data
TEST_CLIENT = {
    "email": "test@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "1234567890"
}

TEST_LOGIN = {
    "email": "test@example.com",
    "password": "testpass123"
}

@pytest.fixture()
def test_login(db_session: Session):
    client_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "1234567890"
    }

    hashed_password = hash_password(client_data["password"])
    client = Client(
        email=client_data["email"],
        password_hash=hashed_password,
        first_name=client_data["first_name"],
        last_name=client_data["last_name"],
        phone_number=client_data["phone_number"],
    )
    db_session.add(client)
    db_session.commit()
    return client

# Fixtures
@pytest.fixture
def test_client(db_session: Session):
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:6]}@example.com"

    client_data = {
        "email": unique_email,
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "1234567890"
    }

    hashed_password = hash_password(client_data["password"])
    client = Client(
        email=client_data["email"],
        password_hash=hashed_password,
        first_name=client_data["first_name"],
        last_name=client_data["last_name"],
        phone_number=client_data["phone_number"],
    )
    db_session.add(client)
    db_session.commit()
    return client


# Tests
def test_login_success(db_session: Session, test_login: Client):
    print(db_session.query(User).all()[0].email)
    response = client.post(
        "/auth/login",
        json=TEST_LOGIN,
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials(db_session: Session):
    response = client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_signup_success(db_session: Session):
    import uuid
    unique_email = f"new_{uuid.uuid4().hex[:6]}@test.com"

    new_user = {
        "email": unique_email,
        "password": "newpass123",
        "first_name": "New",
        "last_name": "User",
        "phone_number": "9876543210"
    }

    response = client.post(
        "/auth/signup",
        json=new_user,
    )

    assert response.status_code == 201
    assert response.json()["message"] == "User created successfully"
    print(db_session.query(User).all())
    db_user = db_session.query(User).filter_by(email=unique_email).first()
    assert db_user is not None


def test_signup_duplicate_email(db_session: Session, test_login: Client):
    response = client.post(
        "/auth/signup",
        json=TEST_CLIENT,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "A user with this email already exists"


def test_get_me(db_session: Session, test_login: Client):
    login_response = client.post(
        "/auth/login",
        json=TEST_LOGIN,
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["email"] == TEST_CLIENT["email"]


def test_get_me_unauthorized():
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_admin_endpoint_unauthorized(db_session: Session, test_login: Client):
    login_response = client.post(
        "/auth/login",
        json=TEST_LOGIN,
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/admin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403