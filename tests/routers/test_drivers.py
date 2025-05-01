import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Driver, Dispatcher, Vehicle
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

TEST_VEHICLE = {
    "model": "Tesla Model 3",
    "license_plate": "AA1234BB",
    "capacity": 5,
    "mileage": 15000
}


@pytest.fixture
def test_vehicle(db_session: Session):
    vehicle = Vehicle(**TEST_VEHICLE)
    db_session.add(vehicle)
    db_session.commit()
    return vehicle


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
def dispatcher_auth_headers(test_dispatcher):
    login_data = {
        "email": TEST_DISPATCHER["email"],
        "password": TEST_DISPATCHER["password"]
    }
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_driver_success(db_session: Session, dispatcher_auth_headers):
    driver_data = {
        "email": "new.driver@example.com",
        "password": "newpass123",
        "first_name": "New",
        "last_name": "Driver",
        "license_number": "DL98765432"
    }

    response = client.post(
        "/drivers/",
        json=driver_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 201
    assert response.json()["email"] == driver_data["email"]
    assert response.json()["license_number"] == driver_data["license_number"]

    db_driver = db_session.query(Driver).filter_by(email=driver_data["email"]).first()
    assert db_driver is not None


def test_create_driver_duplicate_email(db_session: Session, test_driver, dispatcher_auth_headers):
    driver_data = {
        "email": TEST_DRIVER["email"],
        "password": "anypassword",
        "first_name": "Duplicate",
        "last_name": "Driver",
        "license_number": "DL00000000"
    }

    response = client.post(
        "/drivers/",
        json=driver_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_driver_with_vehicle(db_session: Session, dispatcher_auth_headers, test_vehicle):
    driver_data = {
        "email": "new.driver@example.com",
        "password": "newpass123",
        "first_name": "New",
        "last_name": "Driver",
        "license_number": "DL98765432",
        "vehicle_id": test_vehicle.id
    }

    response = client.post(
        "/drivers/",
        json=driver_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 201
    assert response.json()["vehicle_id"] == test_vehicle.id

    driver = db_session.query(Driver).filter_by(email=driver_data["email"]).first()
    assert driver.vehicle_id == test_vehicle.id


def test_update_driver_vehicle(db_session: Session, test_driver, test_vehicle, dispatcher_auth_headers):
    new_vehicle = Vehicle(
        model="Nissan Leaf",
        license_plate="CC5678DD",
        capacity=4,
        mileage=20000
    )
    db_session.add(new_vehicle)
    db_session.commit()

    update_data = {"vehicle_id": new_vehicle.id}

    response = client.patch(
        f"/drivers/{test_driver.id}",
        json=update_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    db_session.refresh(test_driver)
    assert test_driver.vehicle_id == new_vehicle.id


def test_update_driver_with_invalid_vehicle(db_session: Session, test_driver, dispatcher_auth_headers):
    update_data = {"vehicle_id": 9999}  # Неіснуючий vehicle_id

    response = client.patch(
        f"/drivers/{test_driver.id}",
        json=update_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 404
    assert "Vehicle not found" in response.json()["detail"]


def test_list_drivers(db_session: Session, test_driver, dispatcher_auth_headers):
    response = client.get("/drivers/", headers=dispatcher_auth_headers)

    assert response.status_code == 200
    drivers = response.json()
    assert len(drivers) >= 1
    assert any(d["email"] == TEST_DRIVER["email"] for d in drivers)


def test_get_driver_success(db_session: Session, test_driver, dispatcher_auth_headers):
    response = client.get(
        f"/drivers/{test_driver.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["email"] == TEST_DRIVER["email"]
    assert response.json()["license_number"] == TEST_DRIVER["license_number"]


def test_get_driver_not_found(db_session: Session, dispatcher_auth_headers):
    non_existent_id = 9999
    response = client.get(
        f"/drivers/{non_existent_id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_driver_success(db_session: Session, test_driver, dispatcher_auth_headers):
    update_data = {
        "first_name": "Updated",
        "last_name": "Driver",
        "license_number": "DL99999999"
    }

    response = client.patch(
        f"/drivers/{test_driver.id}",
        json=update_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"
    assert response.json()["license_number"] == "DL99999999"

    db_session.refresh(test_driver)
    assert test_driver.first_name == "Updated"
    assert test_driver.license_number == "DL99999999"


def test_update_driver_not_found(db_session: Session, dispatcher_auth_headers):
    non_existent_id = 9999
    update_data = {
        "first_name": "Updated",
        "license_number": "DL99999999"
    }

    response = client.patch(
        f"/drivers/{non_existent_id}",
        json=update_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_driver_success(db_session: Session, test_driver, dispatcher_auth_headers):
    response = client.delete(
        f"/drivers/{test_driver.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 204
    db_driver = db_session.query(Driver).filter_by(id=test_driver.id).first()
    assert db_driver is None


def test_delete_driver_not_found(db_session: Session, dispatcher_auth_headers):
    non_existent_id = 9999
    response = client.delete(
        f"/drivers/{non_existent_id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
