from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import LogBreak, Driver, Dispatcher, Delivery, Client, Location
from app.utils.security import hash_password

client = TestClient(app)

TEST_DRIVER = {
    "email": "driver@example.com",
    "password": "driverpass123",
    "first_name": "Driver",
    "last_name": "Test",
    "license_number": "DL12345678"
}

TEST_DISPATCHER = {
    "email": "dispatcher@example.com",
    "password": "dispatcherpass123",
    "first_name": "Dispatcher",
    "last_name": "Test"
}

TEST_CLIENT = {
    "email": "client@example.com",
    "password": "clientpass123",
    "first_name": "Client",
    "last_name": "Test",
    "phone_number": "+1234567890"
}

TEST_DELIVERY = {
    "pickup_location": "123 Main St",
    "dropoff_location": "456 Oak Ave",
    "package_details": "Test package",
    "status": "Pending"
}

TEST_LOG_BREAK = {
    "location": {
        "latitude": 49.8397,
        "longitude": 24.0297,
        "address": "Rest Area"
    },
    "start_time": datetime.now(),
    "end_time": datetime.now() + timedelta(minutes=30),
    "cost": 15.50
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
def test_driver(db_session: Session):
    hashed_password = hash_password(TEST_DRIVER["password"])
    driver = Driver(
        email=TEST_DRIVER["email"],
        password_hash=hashed_password,
        first_name=TEST_DRIVER["first_name"],
        last_name=TEST_DRIVER["last_name"],
        license_number=TEST_DRIVER["license_number"]
    )
    db_session.add(driver)
    db_session.commit()
    return driver


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
def test_delivery(db_session: Session, test_driver, test_client):
    delivery = Delivery(
        **TEST_DELIVERY,
        driver_id=test_driver.id,
        client_id=test_client.id
    )
    db_session.add(delivery)
    db_session.commit()
    return delivery


@pytest.fixture
def test_location(db_session: Session):
    location = Location(
        latitude=TEST_LOG_BREAK["location"]["latitude"],
        longitude=TEST_LOG_BREAK["location"]["longitude"],
        address=TEST_LOG_BREAK["location"]["address"]
    )
    db_session.add(location)
    db_session.commit()
    return location


@pytest.fixture
def test_log_break(db_session: Session, test_delivery, test_location):
    log_break = LogBreak(
        start_time=TEST_LOG_BREAK["start_time"],
        end_time=TEST_LOG_BREAK["end_time"],
        cost=TEST_LOG_BREAK["cost"],
        delivery_id=test_delivery.id,
        location_id=test_location.id
    )
    db_session.add(log_break)
    db_session.commit()
    return log_break


@pytest.fixture
def driver_auth_headers(test_driver):
    login_data = {
        "email": TEST_DRIVER["email"],
        "password": TEST_DRIVER["password"]
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


def test_create_log_break_success(db_session: Session, driver_auth_headers, test_delivery):
    log_break_data = {
        "location": TEST_LOG_BREAK["location"],
        "start_time": TEST_LOG_BREAK["start_time"].isoformat(),
        "end_time": TEST_LOG_BREAK["end_time"].isoformat(),
        "cost": TEST_LOG_BREAK["cost"],
        "delivery_id": test_delivery.id
    }

    response = client.post("/log_breaks/", json=log_break_data, headers=driver_auth_headers)
    assert response.status_code == 201
    data = response.json()

    assert isinstance(data["location"], dict)
    assert data["location"]["address"] == TEST_LOG_BREAK["location"]["address"]
    assert data["location"]["latitude"] == TEST_LOG_BREAK["location"]["latitude"]
    assert data["delivery_id"] == test_delivery.id

    db_log_break = db_session.query(LogBreak).filter_by(id=data["id"]).first()
    assert db_log_break is not None


def test_create_log_break_unauthorized(db_session: Session, test_delivery):
    log_break_data = {
        "location": TEST_LOG_BREAK["location"],
        "start_time": TEST_LOG_BREAK["start_time"].isoformat(),
        "end_time": TEST_LOG_BREAK["end_time"].isoformat(),
        "cost": TEST_LOG_BREAK["cost"],
        "delivery_id": test_delivery.id
    }

    response = client.post("/log_breaks/", json=log_break_data)
    assert response.status_code == 401


def test_create_log_break_wrong_driver(db_session: Session, driver_auth_headers):
    delivery = Delivery(**TEST_DELIVERY)
    db_session.add(delivery)
    db_session.commit()

    log_break_data = {
        "location": TEST_LOG_BREAK["location"],
        "start_time": TEST_LOG_BREAK["start_time"].isoformat(),
        "end_time": TEST_LOG_BREAK["end_time"].isoformat(),
        "cost": TEST_LOG_BREAK["cost"],
        "delivery_id": delivery.id
    }

    response = client.post("/log_breaks/", json=log_break_data, headers=driver_auth_headers)
    assert response.status_code == 404
    assert "not assigned to you" in response.json()["detail"]


def test_list_log_breaks(db_session: Session, test_log_break):
    response = client.get("/log_breaks/")
    assert response.status_code == 200
    log_breaks = response.json()
    assert len(log_breaks) >= 1
    assert any(lb["id"] == test_log_break.id for lb in log_breaks)


def test_get_log_break_success(db_session: Session, test_log_break):
    response = client.get(f"/log_breaks/{test_log_break.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_log_break.id
    assert data["location"]["address"] == test_log_break.location.address


def test_update_log_break_success(db_session: Session, driver_auth_headers, test_log_break):
    update_data = {
        "location": {
            "latitude": 50.4501,
            "longitude": 30.5234,
            "address": "Kyiv Rest Spot"
        },
        "cost": 20.00
    }

    response = client.patch(
        f"/log_breaks/{test_log_break.id}",
        json=update_data,
        headers=driver_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["location"]["address"] == update_data["location"]["address"]
    assert data["cost"] == update_data["cost"]

    db_session.refresh(test_log_break)
    assert test_log_break.location.address == update_data["location"]["address"]


def test_update_log_break_unauthorized(db_session: Session, dispatcher_auth_headers, test_log_break):
    update_data = {"location": {"address": "Should Fail", "latitude": 0.0, "longitude": 0.0}}
    response = client.patch(
        f"/log_breaks/{test_log_break.id}",
        json=update_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 403


def test_delete_log_break_success(db_session: Session, driver_auth_headers, test_log_break):
    response = client.delete(
        f"/log_breaks/{test_log_break.id}",
        headers=driver_auth_headers
    )

    assert response.status_code == 204
    assert db_session.query(LogBreak).filter_by(id=test_log_break.id).first() is None


def test_delete_log_break_unauthorized(db_session: Session, dispatcher_auth_headers, test_log_break):
    response = client.delete(
        f"/log_breaks/{test_log_break.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 403
    assert db_session.query(LogBreak).filter_by(id=test_log_break.id).first() is not None
