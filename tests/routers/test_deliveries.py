import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Delivery, Driver, Dispatcher, Admin, Client
from app.utils.security import hash_password
from app.schemas.delivery import DeliveryStatus

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

TEST_ADMIN = {
    "email": "admin@example.com",
    "password": "adminpass123",
    "first_name": "Admin",
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
    "package_details": "Fragile package",
    "status": DeliveryStatus.PENDING
}


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


@pytest.fixture
def driver_auth_headers(test_driver):
    login_data = {
        "email": TEST_DRIVER["email"],
        "password": TEST_DRIVER["password"]
    }
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Delivery CRUD Tests
def test_create_delivery_success(db_session: Session, dispatcher_auth_headers, test_driver, test_client):
    delivery_data = {
        **TEST_DELIVERY,
        "driver_id": test_driver.id,
        "client_id": test_client.id
    }

    response = client.post(
        "/deliveries/",
        json=delivery_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["pickup_location"] == delivery_data["pickup_location"]
    assert data["status"] == DeliveryStatus.PENDING

    db_delivery = db_session.query(Delivery).filter_by(id=data["id"]).first()
    assert db_delivery is not None


def test_create_delivery_unauthorized(db_session: Session, test_driver, test_client):
    delivery_data = {
        **TEST_DELIVERY,
        "driver_id": test_driver.id,
        "client_id": test_client.id
    }

    response = client.post("/deliveries/", json=delivery_data)
    assert response.status_code == 401


def test_list_deliveries(db_session: Session, dispatcher_auth_headers, test_delivery):
    response = client.get("/deliveries/", headers=dispatcher_auth_headers)

    assert response.status_code == 200
    deliveries = response.json()
    assert len(deliveries) == 1
    assert deliveries[0]["id"] == test_delivery.id


def test_get_delivery_success(db_session: Session, dispatcher_auth_headers, test_delivery):
    response = client.get(
        f"/deliveries/{test_delivery.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_delivery.id
    assert data["status"] == test_delivery.status.value


def test_update_delivery_success(db_session: Session, dispatcher_auth_headers, test_delivery):
    update_data = {
        "pickup_location": "Updated Address",
        "package_details": "Updated details"
    }

    response = client.put(
        f"/deliveries/{test_delivery.id}",
        json=update_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["pickup_location"] == update_data["pickup_location"]

    db_session.refresh(test_delivery)
    assert test_delivery.pickup_location == update_data["pickup_location"]


# Status Update Tests
def test_update_status_success(db_session: Session, driver_auth_headers, test_delivery):
    response = client.patch(
        f"/deliveries/{test_delivery.id}/status",
        json={"new_status": DeliveryStatus.IN_TRANSIT},
        headers=driver_auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == DeliveryStatus.IN_TRANSIT

    db_session.refresh(test_delivery)
    assert test_delivery.status == DeliveryStatus.IN_TRANSIT


def test_update_status_unauthorized(db_session: Session, dispatcher_auth_headers, test_delivery):
    response = client.patch(
        f"/deliveries/{test_delivery.id}/status",
        json={"new_status": DeliveryStatus.IN_TRANSIT},
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 403


def test_update_status_wrong_driver(db_session: Session, driver_auth_headers):
    # Create a new delivery with no driver assigned
    delivery = Delivery(**TEST_DELIVERY)
    db_session.add(delivery)
    db_session.commit()

    response = client.patch(
        f"/deliveries/{delivery.id}/status",
        json={"new_status": DeliveryStatus.IN_TRANSIT},
        headers=driver_auth_headers
    )

    assert response.status_code == 403


# Delete Tests
def test_delete_delivery_success(db_session: Session, admin_auth_headers, test_delivery):
    response = client.delete(
        f"/deliveries/{test_delivery.id}",
        headers=admin_auth_headers
    )

    assert response.status_code == 204
    assert db_session.query(Delivery).filter_by(id=test_delivery.id).first() is None


def test_delete_delivery_unauthorized(db_session: Session, dispatcher_auth_headers, test_delivery):
    response = client.delete(
        f"/deliveries/{test_delivery.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 403
    assert db_session.query(Delivery).filter_by(id=test_delivery.id).first() is not None