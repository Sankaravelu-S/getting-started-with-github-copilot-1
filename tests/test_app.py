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
    # disable auto-follow so we can inspect the redirect response
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/static/index.html"


# ---- activities listing ----------------------------------------------------

def test_get_activities(client):
    response = client.get("/activities")
    assert response.status_code == 200
    assert response.json() == app_module.activities


# ---- signup endpoint -------------------------------------------------------

def test_signup_success(client):
    name = "Chess Club"
    email = "newstudent@mergington.edu"
    response = client.post(f"/activities/{name}/signup", params={"email": email})
    assert response.status_code == 200
    assert email in app_module.activities[name]["participants"]
    assert response.json()["message"] == f"Signed up {email} for {name}"


def test_signup_nonexistent_activity(client):
    response = client.post("/activities/NotExist/signup", params={"email": "foo@bar"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate(client):
    name = "Programming Class"
    email = app_module.activities[name]["participants"][0]
    response = client.post(f"/activities/{name}/signup", params={"email": email})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


# ---- removal endpoint ------------------------------------------------------

def test_remove_participant_success(client):
    name = "Chess Club"
    email = app_module.activities[name]["participants"][0]
    response = client.delete(f"/activities/{name}/participants", params={"email": email})
    assert response.status_code == 200
    assert email not in app_module.activities[name]["participants"]
    assert response.json()["message"] == f"Removed {email} from {name}"


def test_remove_nonexistent_activity(client):
    response = client.delete("/activities/NotExist/participants", params={"email": "foo@bar"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_nonparticipant(client):
    name = "Tennis Club"
    response = client.delete(f"/activities/{name}/participants", params={"email": "ghost@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
