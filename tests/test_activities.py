import copy
import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture(autouse=True)
def isolate_activities():
    # Arrange: backup the global activities state
    backup = copy.deepcopy(app_module.activities)
    try:
        yield
    finally:
        # Teardown: restore activities to original state
        app_module.activities.clear()
        app_module.activities.update(backup)


def test_get_activities_returns_expected_structure(client):
    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    sample = data["Chess Club"]
    assert "description" in sample
    assert "schedule" in sample
    assert "max_participants" in sample
    assert "participants" in sample


def test_signup_success_adds_participant(client):
    # Arrange
    activity = "Basketball Team"
    email = "test_student@mergington.edu"
    before = list(app_module.activities[activity]["participants"])

    # Act
    resp = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")
    after = app_module.activities[activity]["participants"]
    assert email in after
    assert len(after) == len(before) + 1


def test_signup_duplicate_returns_400(client):
    # Arrange
    activity = "Chess Club"
    existing_email = app_module.activities[activity]["participants"][0]

    # Act
    resp = client.post(f"/activities/{activity}/signup?email={existing_email}")

    # Assert
    assert resp.status_code == 400
    body = resp.json()
    assert "already signed up" in body.get("detail", "")


def test_signup_nonexistent_activity_returns_404(client):
    # Arrange
    fake_activity = "Nonexistent Club"
    email = "someone@nowhere.edu"

    # Act
    resp = client.post(f"/activities/{fake_activity}/signup?email={email}")

    # Assert
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Activity not found"
