import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, UTC

from app.main import app
from app.models import Review, Delivery, Client, Driver, Dispatcher, Location
from app.utils.security import hash_password

client = TestClient(app)

TEST_REVIEW = {
    "text": "Great service!",
    "rating": 5
}

TEST_CLIENT = {
    "email": "client@example.com",
    "password": "clientpass123",
    "first_name": "Client",
    "last_name": "Test",
    "phone_number": "+1234567890"
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

TEST_DELIVERY = {
    "package_details": "Test package",
    "status": "Pending"
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
    pickup_location = Location(
        latitude=50.4501,
        longitude=30.5234,
        address="123 Main St, Kyiv"
    )
    dropoff_location = Location(
        latitude=50.4547,
        longitude=30.5038,
        address="456 Oak Ave, Kyiv"
    )
    db_session.add_all([pickup_location, dropoff_location])
    db_session.commit()

    delivery = Delivery(
        **TEST_DELIVERY,
        driver_id=test_driver.id,
        client_id=test_client.id,
        pickup_location_id=pickup_location.id,
        dropoff_location_id=dropoff_location.id,
        created_at=datetime.now(UTC)
    )
    db_session.add(delivery)
    db_session.commit()
    return delivery


@pytest.fixture
def test_review(db_session: Session, test_delivery):
    review = Review(
        **TEST_REVIEW,
        delivery_id=test_delivery.id,
        created_at=datetime.now(UTC)
    )
    db_session.add(review)
    db_session.commit()
    return review


@pytest.fixture
def client_auth_headers(test_client):
    login_data = {
        "email": TEST_CLIENT["email"],
        "password": TEST_CLIENT["password"]
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


def test_create_review_success(db_session: Session, client_auth_headers, test_delivery):
    review_data = {
        "delivery_id": test_delivery.id,
        "text": "Excellent service!",
        "rating": 5
    }

    response = client.post(
        "/reviews/",
        json=review_data,
        headers=client_auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["text"] == review_data["text"]
    assert data["rating"] == review_data["rating"]
    assert data["delivery_id"] == test_delivery.id

    db_review = db_session.query(Review).filter_by(id=data["id"]).first()
    assert db_review is not None


def test_create_review_unauthorized(db_session: Session, test_delivery):
    review_data = {
        "delivery_id": test_delivery.id,
        "text": "Should fail",
        "rating": 1
    }

    response = client.post("/reviews/", json=review_data)
    assert response.status_code == 401


def test_create_review_duplicate(db_session: Session, client_auth_headers, test_review):
    review_data = {
        "delivery_id": test_review.delivery_id,
        "text": "Duplicate review",
        "rating": 3
    }

    response = client.post(
        "/reviews/",
        json=review_data,
        headers=client_auth_headers
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_review_wrong_client(db_session: Session, client_auth_headers, test_driver):
    other_client = Client(
        email="other@example.com",
        password_hash=hash_password("otherpass123"),
        first_name="Other",
        last_name="Client",
        phone_number="+9876543210"
    )
    db_session.add(other_client)
    db_session.commit()

    pickup_location = Location(
        latitude=50.4600,
        longitude=30.5200,
        address="789 New St, Kyiv"
    )
    dropoff_location = Location(
        latitude=50.4700,
        longitude=30.5300,
        address="101 New Ave, Kyiv"
    )
    db_session.add_all([pickup_location, dropoff_location])
    db_session.commit()

    delivery = Delivery(
        package_details="Other package",
        status="Pending",
        driver_id=test_driver.id,
        client_id=other_client.id,
        pickup_location_id=pickup_location.id,
        dropoff_location_id=dropoff_location.id
    )
    db_session.add(delivery)
    db_session.commit()

    review_data = {
        "delivery_id": delivery.id,
        "text": "Should fail",
        "rating": 2
    }

    response = client.post(
        "/reviews/",
        json=review_data,
        headers=client_auth_headers
    )

    assert response.status_code == 404
    assert "not assigned to you" in response.json()["detail"]


def test_list_reviews(db_session: Session, test_review, dispatcher_auth_headers):
    response = client.get("/reviews/", headers=dispatcher_auth_headers)

    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 1
    assert reviews[0]["id"] == test_review.id


def test_list_reviews_filter_by_delivery(db_session: Session, test_review, dispatcher_auth_headers, test_driver,
                                         test_client):
    pickup_location = Location(
        latitude=50.4600,
        longitude=30.5200,
        address="789 New St, Kyiv"
    )
    dropoff_location = Location(
        latitude=50.4700,
        longitude=30.5300,
        address="101 New Ave, Kyiv"
    )
    db_session.add_all([pickup_location, dropoff_location])
    db_session.commit()

    delivery2 = Delivery(
        package_details="Other package",
        status="Pending",
        driver_id=test_driver.id,
        pickup_location_id=pickup_location.id,
        dropoff_location_id=dropoff_location.id
    )
    db_session.add(delivery2)
    db_session.commit()

    review2 = Review(
        text="Another review",
        rating=4,
        delivery_id=delivery2.id
    )
    db_session.add(review2)
    db_session.commit()

    response = client.get(
        f"/reviews/?delivery_id={test_review.delivery_id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 1
    assert reviews[0]["id"] == test_review.id


def test_get_review_success(db_session: Session, test_review, dispatcher_auth_headers):
    response = client.get(
        f"/reviews/{test_review.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_review.id
    assert data["text"] == test_review.text


def test_get_review_not_found(db_session: Session, dispatcher_auth_headers):
    non_existent_id = 9999
    response = client.get(
        f"/reviews/{non_existent_id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_review_success(db_session: Session, client_auth_headers, test_review):
    update_data = {
        "text": "Updated review text",
        "rating": 4
    }

    response = client.patch(
        f"/reviews/{test_review.id}",
        json=update_data,
        headers=client_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == update_data["text"]
    assert data["rating"] == update_data["rating"]

    db_session.refresh(test_review)
    assert test_review.text == update_data["text"]


def test_update_review_unauthorized(db_session: Session, dispatcher_auth_headers, test_review):
    update_data = {"text": "Should fail"}

    response = client.patch(
        f"/reviews/{test_review.id}",
        json=update_data,
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 403


def test_delete_review_success(db_session: Session, client_auth_headers, test_review):
    response = client.delete(
        f"/reviews/{test_review.id}",
        headers=client_auth_headers
    )

    assert response.status_code == 204
    assert db_session.query(Review).filter_by(id=test_review.id).first() is None


def test_delete_review_unauthorized(db_session: Session, dispatcher_auth_headers, test_review):
    response = client.delete(
        f"/reviews/{test_review.id}",
        headers=dispatcher_auth_headers
    )

    assert response.status_code == 403
    assert db_session.query(Review).filter_by(id=test_review.id).first() is not None


def test_get_my_reviews(db_session: Session, client_auth_headers, test_review, test_driver):
    other_client = Client(
        email="other@example.com",
        password_hash=hash_password("otherpass123"),
        first_name="Other",
        last_name="Client",
        phone_number="+9876543210"
    )
    db_session.add(other_client)
    db_session.commit()

    pickup_location = Location(
        latitude=50.4600,
        longitude=30.5200,
        address="789 New St, Kyiv"
    )
    dropoff_location = Location(
        latitude=50.4700,
        longitude=30.5300,
        address="101 New Ave, Kyiv"
    )
    db_session.add_all([pickup_location, dropoff_location])
    db_session.commit()

    delivery = Delivery(
        package_details="Other package",
        status="Pending",
        driver_id=test_driver.id,
        client_id=other_client.id,
        pickup_location_id=pickup_location.id,
        dropoff_location_id=dropoff_location.id
    )
    db_session.add(delivery)
    db_session.commit()

    other_review = Review(
        text="Other review",
        rating=3,
        delivery_id=delivery.id
    )
    db_session.add(other_review)
    db_session.commit()

    response = client.get(
        "/reviews/client/me",
        headers=client_auth_headers
    )

    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 1
    assert reviews[0]["id"] == test_review.id
