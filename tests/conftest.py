"""Pytest configuration and fixtures for API tests."""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def sample_activities():
    """Provide fresh sample activities data for each test."""
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 2,  # Small capacity to test "full" scenario
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
    }


@pytest.fixture
def app_with_test_data(sample_activities, monkeypatch):
    """Replace the app's activities dict with test data."""
    import src.app
    monkeypatch.setattr(src.app, 'activities', sample_activities)
    return app


@pytest.fixture
def client(app_with_test_data):
    """Provide a TestClient for making requests to the app."""
    return TestClient(app_with_test_data)
