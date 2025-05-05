import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Delivery, Driver, Dispatcher, Admin, Client, Location
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

TEST_PICKUP_LOCATION = {
    "latitude": 50.4501,
    "longitude": 30.5234,
    "address": "123 Main St, Kyiv"
}

TEST_DROPOFF_LOCATION = {
    "latitude": 50.4547,
    "longitude": 30.5038,
    "address": "456 Oak Ave, Kyiv"
}

TEST_DELIVERY = {
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
def test_pickup_location(db_session: Session):
    location = Location(**TEST_PICKUP_LOCATION)
    db_session.add(location)
    db_session.commit()
    return location


@pytest.fixture
def test_dropoff_location(db_session: Session):
    location = Location(**TEST_DROPOFF_LOCATION)
    db_session.add(location)
    db_session.commit()
    return location


@pytest.fixture
def test_delivery(db_session: Session, test_driver, test_client, test_pickup_location, test_dropoff_location):
    delivery = Delivery(
        **TEST_DELIVERY,
        driver_id=test_driver.id,
        client_id=test_client.id,
        pickup_location_id=test_pickup_location.id,
        dropoff_location_id=test_dropoff_location.id
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


def test_create_delivery_success(db_session: Session, dispatcher_auth_headers, test_driver, test_client):
    delivery_data = {
        **TEST_DELIVERY,
        "driver_id": test_driver.id,
        "client_id": test_client.id,
        "pickup_location": TEST_PICKUP_LOCATION,
        "dropoff_location": TEST_DROPOFF_LOCATION
    }

    response = client.post(
        "/deliveries/",
        json=delivery_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["pickup_location"]["latitude"] == TEST_PICKUP_LOCATION["latitude"]
    assert data["status"] == DeliveryStatus.PENDING

    db_delivery = db_session.query(Delivery).filter_by(id=data["id"]).first()
    assert db_delivery is not None


def test_list_deliveries(db_session: Session, dispatcher_auth_headers, test_delivery):
    response = client.get("/deliveries/", headers=dispatcher_auth_headers)

    assert response.status_code == 200
    deliveries = response.json()
    assert len(deliveries) == 1
    assert deliveries[0]["id"] == test_delivery.id
    assert deliveries[0]["pickup_location"]["id"] == test_delivery.pickup_location_id


def test_get_delivery_success(db_session: Session, dispatcher_auth_headers, test_delivery):
    response = client.get(
        f"/deliveries/{test_delivery.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_delivery.id
    assert data["pickup_location"]["id"] == test_delivery.pickup_location_id
    assert data["dropoff_location"]["id"] == test_delivery.dropoff_location_id


def test_update_delivery_success(db_session: Session, dispatcher_auth_headers, test_delivery):
    new_location = {
        "latitude": 50.4600,
        "longitude": 30.5200,
        "address": "New location address"
    }

    update_data = {
        "pickup_location": new_location,
        "package_details": "Updated details"
    }

    response = client.patch(
        f"/deliveries/{test_delivery.id}",
        json=update_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["pickup_location"]["latitude"] == new_location["latitude"]

    db_session.refresh(test_delivery)
    assert test_delivery.pickup_location.latitude == new_location["latitude"]


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


def test_delete_delivery_success(db_session: Session, admin_auth_headers, test_delivery):
    pickup_id = test_delivery.pickup_location_id
    dropoff_id = test_delivery.dropoff_location_id

    response = client.delete(
        f"/deliveries/{test_delivery.id}",
        headers=admin_auth_headers
    )

    assert response.status_code == 204
    assert db_session.query(Delivery).filter_by(id=test_delivery.id).first() is None
    # Verify locations are not deleted (if that's your business logic)
    assert db_session.query(Location).filter_by(id=pickup_id).first() is not None
    assert db_session.query(Location).filter_by(id=dropoff_id).first() is not None


def test_get_my_deliveries_as_driver(db_session: Session, driver_auth_headers, test_delivery):
    response = client.get(
        "/deliveries/driver/me",
        headers=driver_auth_headers
    )

    assert response.status_code == 200
    deliveries = response.json()
    assert len(deliveries) == 1
    assert deliveries[0]["id"] == test_delivery.id
    assert deliveries[0]["driver_id"] == test_delivery.driver_id


def test_get_my_deliveries_as_client(db_session: Session, test_client, test_delivery):
    # Login as client
    login_data = {
        "email": TEST_CLIENT["email"],
        "password": TEST_CLIENT["password"]
    }
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        "/deliveries/client/me",
        headers=headers
    )

    assert response.status_code == 200
    deliveries = response.json()
    assert len(deliveries) == 1
    assert deliveries[0]["id"] == test_delivery.id
    assert deliveries[0]["client_id"] == test_delivery.client_id