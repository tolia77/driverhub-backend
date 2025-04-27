import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models import Dispatcher, Admin
from app.utils.security import hash_password

client = TestClient(app)

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
def admin_auth_headers(test_admin):
    login_data = {
        "email": TEST_ADMIN["email"],
        "password": TEST_ADMIN["password"]
    }
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def dispatcher_auth_headers(test_dispatcher):
    login_data = {
        "email": TEST_DISPATCHER["email"],
        "password": TEST_DISPATCHER["password"]
    }
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_dispatcher_success(db_session: Session, admin_auth_headers):
    dispatcher_data = {
        "email": "new.dispatcher@example.com",
        "password": "newpass123",
        "first_name": "New",
        "last_name": "Dispatcher"
    }
    response = client.post(
        "/dispatchers/",
        json=dispatcher_data,
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    assert response.json()["email"] == dispatcher_data["email"]
    db_dispatcher = db_session.query(Dispatcher).filter_by(email=dispatcher_data["email"]).first()
    assert db_dispatcher is not None


def test_create_dispatcher_duplicate_email(db_session: Session, test_dispatcher, admin_auth_headers):
    dispatcher_data = {
        "email": TEST_DISPATCHER["email"],
        "password": "anypassword",
        "first_name": "Duplicate",
        "last_name": "Dispatcher"
    }
    response = client.post(
        "/dispatchers/",
        json=dispatcher_data,
        headers=admin_auth_headers
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_list_dispatchers(db_session: Session, test_dispatcher, admin_auth_headers):
    response = client.get("/dispatchers/", headers=admin_auth_headers)
    assert response.status_code == 200
    dispatchers = response.json()
    assert len(dispatchers) >= 1
    assert any(d["email"] == TEST_DISPATCHER["email"] for d in dispatchers)


def test_get_dispatcher_success(db_session: Session, test_dispatcher, admin_auth_headers):
    response = client.get(
        f"/dispatchers/{test_dispatcher.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert response.json()["email"] == TEST_DISPATCHER["email"]


def test_get_dispatcher_not_found(db_session: Session, admin_auth_headers):
    non_existent_id = 9999
    response = client.get(
        f"/dispatchers/{non_existent_id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_dispatcher_success(db_session: Session, test_dispatcher, admin_auth_headers):
    update_data = {
        "first_name": "Updated",
        "last_name": "Name"
    }
    response = client.put(
        f"/dispatchers/{test_dispatcher.id}",
        json=update_data,
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"
    db_session.refresh(test_dispatcher)
    assert test_dispatcher.first_name == "Updated"


def test_update_dispatcher_not_found(db_session: Session, admin_auth_headers):
    non_existent_id = 9999
    update_data = {
        "first_name": "Updated",
        "last_name": "Name"
    }
    response = client.put(
        f"/dispatchers/{non_existent_id}",
        json=update_data,
        headers=admin_auth_headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_dispatcher_success(db_session: Session, test_dispatcher, admin_auth_headers):
    response = client.delete(
        f"/dispatchers/{test_dispatcher.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 204
    db_dispatcher = db_session.query(Dispatcher).filter_by(id=test_dispatcher.id).first()
    assert db_dispatcher is None


def test_delete_dispatcher_not_admin(db_session: Session, test_dispatcher, dispatcher_auth_headers):
    response = client.delete(
        f"/dispatchers/{test_dispatcher.id}",
        headers=dispatcher_auth_headers
    )
    assert response.status_code == 403
    db_dispatcher = db_session.query(Dispatcher).filter_by(id=test_dispatcher.id).first()
    assert db_dispatcher is not None


def test_delete_dispatcher_not_found(db_session: Session, admin_auth_headers):
    non_existent_id = 9999
    response = client.delete(
        f"/dispatchers/{non_existent_id}",
        headers=admin_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
