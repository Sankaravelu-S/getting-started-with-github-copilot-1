from fastapi.testclient import TestClient
import pytest

from src import app as app_module

# make a deep copy of the original activities so we can restore it
_original_activities = {k: v.copy() for k, v in app_module.activities.items()}


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activity data before each test."""
    # shallow copy of each activity dictionary is sufficient for our tests
    app_module.activities.clear()
    for name, details in _original_activities.items():
        app_module.activities[name] = details.copy()


@pytest.fixture

def client():
    return TestClient(app_module.app)


# ---- root redirect ---------------------------------------------------------

def test_root_redirects(client):
    # Arrange: client fixture provided
    # Act: perform GET without following redirect
    response = client.get("/", follow_redirects=False)
    # Assert: redirection status and location header
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/static/index.html"


# ---- activities listing ----------------------------------------------------

def test_get_activities(client):
    # Arrange
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    assert response.json() == app_module.activities


# ---- signup endpoint -------------------------------------------------------

def test_signup_success(client):
    # Arrange
    name = "Chess Club"
    email = "newstudent@mergington.edu"
    # Act
    response = client.post(f"/activities/{name}/signup", params={"email": email})
    # Assert
    assert response.status_code == 200
    assert email in app_module.activities[name]["participants"]
    assert response.json()["message"] == f"Signed up {email} for {name}"


def test_signup_nonexistent_activity(client):
    # Arrange
    # Act
    response = client.post("/activities/NotExist/signup", params={"email": "foo@bar"})
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate(client):
    # Arrange
    name = "Programming Class"
    email = app_module.activities[name]["participants"][0]
    # Act
    response = client.post(f"/activities/{name}/signup", params={"email": email})
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


# ---- removal endpoint ------------------------------------------------------

def test_remove_participant_success(client):
    # Arrange
    name = "Chess Club"
    email = app_module.activities[name]["participants"][0]
    # Act
    response = client.delete(f"/activities/{name}/participants", params={"email": email})
    # Assert
    assert response.status_code == 200
    assert email not in app_module.activities[name]["participants"]
    assert response.json()["message"] == f"Removed {email} from {name}"


def test_remove_nonexistent_activity(client):
    # Arrange
    # Act
    response = client.delete("/activities/NotExist/participants", params={"email": "foo@bar"})
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_nonparticipant(client):
    # Arrange
    name = "Tennis Club"
    # Act
    response = client.delete(f"/activities/{name}/participants", params={"email": "ghost@mergington.edu"})
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
