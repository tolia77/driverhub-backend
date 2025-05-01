import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Vehicle, Driver, Dispatcher
from app.utils.security import hash_password

client = TestClient(app)

TEST_VEHICLE = {
    "model": "Tesla Model 3",
    "license_plate": "AA1234BB",
    "capacity": 5,
    "mileage": 15000
}

TEST_DISPATCHER = {
    "email": "dispatcher@example.com",
    "password": "dispatcherpass123",
    "first_name": "Dispatcher",
    "last_name": "Test"
}

TEST_DRIVER = {
    "email": "driver@example.com",
    "password": "driverpass123",
    "first_name": "Driver",
    "last_name": "Test",
    "license_number": "DL12345678"
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


def test_create_vehicle_success(db_session: Session, dispatcher_auth_headers):
    vehicle_data = {
        "model": "Nissan Leaf",
        "license_plate": "CC5678DD",
        "capacity": 4,
        "mileage": 20000
    }

    response = client.post(
        "/vehicles/",
        json=vehicle_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 201
    assert response.json()["license_plate"] == vehicle_data["license_plate"]

    db_vehicle = db_session.query(Vehicle).filter_by(license_plate=vehicle_data["license_plate"]).first()
    assert db_vehicle is not None


def test_create_vehicle_duplicate_license_plate(db_session: Session, test_vehicle, dispatcher_auth_headers):
    vehicle_data = {
        "model": "Tesla Model S",
        "license_plate": TEST_VEHICLE["license_plate"],  # Дублікат
        "capacity": 5,
        "mileage": 10000
    }

    response = client.post(
        "/vehicles/",
        json=vehicle_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_list_vehicles(db_session: Session, test_vehicle, dispatcher_auth_headers):
    response = client.get("/vehicles/", headers=dispatcher_auth_headers)

    assert response.status_code == 200
    vehicles = response.json()
    assert len(vehicles) >= 1
    assert any(v["license_plate"] == TEST_VEHICLE["license_plate"] for v in vehicles)


def test_get_vehicle_success(db_session: Session, test_vehicle, dispatcher_auth_headers):
    response = client.get(
        f"/vehicles/{test_vehicle.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["license_plate"] == TEST_VEHICLE["license_plate"]


def test_get_vehicle_not_found(db_session: Session, dispatcher_auth_headers):
    non_existent_id = 9999
    response = client.get(
        f"/vehicles/{non_existent_id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_vehicle_success(db_session: Session, test_vehicle, dispatcher_auth_headers):
    update_data = {
        "model": "Tesla Model 3 Updated",
        "mileage": 20000
    }

    response = client.patch(
        f"/vehicles/{test_vehicle.id}",
        json=update_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["model"] == "Tesla Model 3 Updated"
    assert response.json()["mileage"] == 20000

    db_session.refresh(test_vehicle)
    assert test_vehicle.model == "Tesla Model 3 Updated"


def test_update_vehicle_duplicate_license_plate(db_session: Session, test_vehicle, dispatcher_auth_headers):
    # Спочатку створимо інший транспорт
    other_vehicle = Vehicle(
        model="Nissan Leaf",
        license_plate="CC5678DD",
        capacity=4,
        mileage=20000
    )
    db_session.add(other_vehicle)
    db_session.commit()

    # Спробуємо змінити номерний знак на вже існуючий
    update_data = {
        "license_plate": other_vehicle.license_plate
    }

    response = client.patch(
        f"/vehicles/{test_vehicle.id}",
        json=update_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 400
    assert "already in use" in response.json()["detail"]


def test_delete_vehicle_success(db_session: Session, test_vehicle, dispatcher_auth_headers):
    response = client.delete(
        f"/vehicles/{test_vehicle.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 204
    db_vehicle = db_session.query(Vehicle).filter_by(id=test_vehicle.id).first()
    assert db_vehicle is None


def test_delete_vehicle_assigned_to_driver(db_session: Session, test_vehicle, dispatcher_auth_headers):
    # Створимо водія і прив'яжемо до транспорту
    driver = Driver(
        email="driver@example.com",
        password_hash=hash_password("driverpass123"),
        first_name="Driver",
        last_name="Test",
        license_number="DL12345678",
        vehicle_id=test_vehicle.id
    )
    db_session.add(driver)
    db_session.commit()

    response = client.delete(
        f"/vehicles/{test_vehicle.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 400
    assert "assigned to a driver" in response.json()["detail"]
    db_vehicle = db_session.query(Vehicle).filter_by(id=test_vehicle.id).first()
    assert db_vehicle is not None


def test_get_unassigned_vehicles(db_session: Session, test_vehicle, test_driver, dispatcher_auth_headers):
    unassigned_vehicle = Vehicle(
        model="Nissan Leaf",
        license_plate="CC5678DD",
        capacity=4,
        mileage=20000
    )
    db_session.add(unassigned_vehicle)

    test_driver.vehicle_id = test_vehicle.id

    db_session.commit()
    response = client.get("/vehicles/unassigned/", headers=dispatcher_auth_headers)

    assert response.status_code == 200
    vehicles = response.json()
    assert any(v["license_plate"] == "CC5678DD" for v in vehicles)
    assert not any(v.get("license_plate") == TEST_VEHICLE["license_plate"] for v in vehicles)
