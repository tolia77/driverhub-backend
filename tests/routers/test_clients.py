import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Client, Dispatcher, Admin
from app.utils.security import hash_password

client = TestClient(app)

TEST_CLIENT = {
    "email": "client@example.com",
    "password": "clientpass123",
    "first_name": "Client",
    "last_name": "Test",
    "phone_number": "+380991234567"
}

TEST_DISPATCHER = {
    "email": "dispatcher@example.com",
    "password": "dispatcherpass123",
    "first_name": "Dispatcher",
    "last_name": "Test"
}

TEST_ADMIN = {
    "email": "admin@example.com",
    "password": "adminpass123",
    "first_name": "Admin",
    "last_name": "Test"
}


@pytest.fixture
def test_client(db_session: Session):
    hashed_password = hash_password(TEST_CLIENT["password"])
    client = Client(
        email=TEST_CLIENT["email"],
        password_hash=hashed_password,
        first_name=TEST_CLIENT["first_name"],
        last_name=TEST_CLIENT["last_name"],
        phone_number=TEST_CLIENT["phone_number"]
    )
    db_session.add(client)
    db_session.commit()
    return client


@pytest.fixture
def test_dispatcher(db_session: Session):
    hashed_password = hash_password(TEST_DISPATCHER["password"])
    dispatcher = Dispatcher(
        email=TEST_DISPATCHER["email"],
        password_hash=hashed_password,
        first_name=TEST_DISPATCHER["first_name"],
        last_name=TEST_DISPATCHER["last_name"]
    )
    db_session.add(dispatcher)
    db_session.commit()
    return dispatcher


@pytest.fixture
def test_admin(db_session: Session):
    hashed_password = hash_password(TEST_ADMIN["password"])
    admin = Admin(
        email=TEST_ADMIN["email"],
        password_hash=hashed_password,
        first_name=TEST_ADMIN["first_name"],
        last_name=TEST_ADMIN["last_name"]
    )
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def dispatcher_auth_headers(test_dispatcher):
    login_data = {
        "email": TEST_DISPATCHER["email"],
        "password": TEST_DISPATCHER["password"]
    }
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(test_admin):
    login_data = {
        "email": TEST_ADMIN["email"],
        "password": TEST_ADMIN["password"]
    }
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_clients(db_session: Session, test_client, dispatcher_auth_headers):
    response = client.get("/clients/", headers=dispatcher_auth_headers)

    assert response.status_code == 200
    clients = response.json()
    assert len(clients) >= 1
    assert any(c["email"] == TEST_CLIENT["email"] for c in clients)


def test_list_clients_unauthorized(db_session: Session):
    # No auth headers
    response = client.get("/clients/")
    assert response.status_code == 401


def test_get_client_success(db_session: Session, test_client, dispatcher_auth_headers):
    response = client.get(
        f"/clients/{test_client.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["email"] == TEST_CLIENT["email"]
    assert response.json()["phone_number"] == TEST_CLIENT["phone_number"]


def test_get_client_not_found(db_session: Session, dispatcher_auth_headers):
    non_existent_id = 9999
    response = client.get(
        f"/clients/{non_existent_id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_client_by_admin_success(db_session: Session, test_client, admin_auth_headers):
    update_data = {
        "first_name": "Updated",
        "last_name": "Client",
        "phone_number": "+380991111111"
    }

    response = client.put(
        f"/clients/{test_client.id}",
        json=update_data,
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"
    assert response.json()["phone_number"] == "+380991111111"

    db_session.refresh(test_client)
    assert test_client.first_name == "Updated"
    assert test_client.phone_number == "+380991111111"


def test_update_client_by_dispatcher_forbidden(db_session: Session, test_client, dispatcher_auth_headers):
    update_data = {"first_name": "Should Fail"}

    response = client.put(
        f"/clients/{test_client.id}",
        json=update_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 403


def test_update_client_not_found(db_session: Session, admin_auth_headers):
    non_existent_id = 9999
    update_data = {"first_name": "Updated"}

    response = client.put(
        f"/clients/{non_existent_id}",
        json=update_data,
        headers=admin_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_client_email_conflict(db_session: Session, test_client, admin_auth_headers):
    # Create another client
    another_client = Client(
        email="another@example.com",
        password_hash="hash",
        first_name="Another",
        last_name="Client",
        phone_number="+380992222222"
    )
    db_session.add(another_client)
    db_session.commit()

    # Try to update test_client's email to another_client's email
    update_data = {"email": another_client.email}

    response = client.put(
        f"/clients/{test_client.id}",
        json=update_data,
        headers=admin_auth_headers
    )

    assert response.status_code == 400
    assert "already in use" in response.json()["detail"]


def test_delete_client_by_admin_success(db_session: Session, test_client, admin_auth_headers):
    response = client.delete(
        f"/clients/{test_client.id}",
        headers=admin_auth_headers
    )

    assert response.status_code == 204
    db_client = db_session.query(Client).filter_by(id=test_client.id).first()
    assert db_client is None


def test_delete_client_by_dispatcher_forbidden(db_session: Session, test_client, dispatcher_auth_headers):
    response = client.delete(
        f"/clients/{test_client.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 403


def test_delete_client_not_found(db_session: Session, admin_auth_headers):
    non_existent_id = 9999
    response = client.delete(
        f"/clients/{non_existent_id}",
        headers=admin_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]