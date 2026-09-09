"""Integration tests for the Mergington High School Activities API."""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Verify GET /activities returns all activities with correct structure."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_returns_correct_structure(self, client):
        """Verify each activity has required fields."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_info in data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)

    def test_get_activities_participant_counts(self, client):
        """Verify participant counts match the test data."""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Programming Class"]["participants"]) == 2
        assert len(data["Gym Class"]["participants"]) == 2


class TestPostSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_participant_success(self, client, sample_activities):
        """Verify successfully signing up a new participant."""
        response = client.post(
            "/activities/Chess Club/signup?email=alice@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up alice@mergington.edu for Chess Club" in data["message"]
        
        # Verify participant was added
        activities = client.get("/activities").json()
        assert "alice@mergington.edu" in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == 3

    def test_signup_duplicate_email_returns_error(self, client):
        """Verify duplicate signup returns 400 error."""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Verify signup for non-existent activity returns 404."""
        response = client.post(
            "/activities/Fake Activity/signup?email=alice@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_full_activity_returns_error(self, client):
        """Verify signup for full activity is not blocked (no capacity check in current code)."""
        # Note: The current app doesn't validate max_participants on signup
        # This test documents that behavior. If capacity checking is added later, update this.
        response = client.post(
            "/activities/Gym Class/signup?email=alice@mergington.edu"
        )
        
        # Currently succeeds because no capacity check is implemented
        assert response.status_code == 200

    def test_signup_updates_participant_count(self, client):
        """Verify participant count increases after signup."""
        activities_before = client.get("/activities").json()
        initial_count = len(activities_before["Programming Class"]["participants"])
        
        client.post("/activities/Programming Class/signup?email=bob@mergington.edu")
        
        activities_after = client.get("/activities").json()
        final_count = len(activities_after["Programming Class"]["participants"])
        
        assert final_count == initial_count + 1


class TestDeleteSignup:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_unregister_existing_participant_success(self, client):
        """Verify successfully unregistering a participant."""
        response = client.delete(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        assert "Unregistered michael@mergington.edu from Chess Club" in response.json()["message"]
        
        # Verify participant was removed
        activities = client.get("/activities").json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == 1

    def test_unregister_nonexistent_participant_returns_error(self, client):
        """Verify unregistering non-existent participant returns 400."""
        response = client.delete(
            "/activities/Chess Club/signup?email=alice@mergington.edu"
        )
        
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """Verify unregistering from non-existent activity returns 404."""
        response = client.delete(
            "/activities/Fake Activity/signup?email=alice@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_updates_participant_count(self, client):
        """Verify participant count decreases after unregister."""
        activities_before = client.get("/activities").json()
        initial_count = len(activities_before["Chess Club"]["participants"])
        
        client.delete("/activities/Chess Club/signup?email=daniel@mergington.edu")
        
        activities_after = client.get("/activities").json()
        final_count = len(activities_after["Chess Club"]["participants"])
        
        assert final_count == initial_count - 1


class TestIntegrationWorkflows:
    """Integration tests combining multiple operations."""

    def test_signup_verify_in_list_then_unregister(self, client):
        """Verify full workflow: signup -> see in list -> unregister."""
        new_email = "charlie@mergington.edu"
        activity_name = "Programming Class"
        
        # Step 1: Verify not yet signed up
        activities = client.get("/activities").json()
        assert new_email not in activities[activity_name]["participants"]
        
        # Step 2: Sign up
        response = client.post(f"/activities/{activity_name}/signup?email={new_email}")
        assert response.status_code == 200
        
        # Step 3: Verify in list
        activities = client.get("/activities").json()
        assert new_email in activities[activity_name]["participants"]
        initial_count = len(activities[activity_name]["participants"])
        
        # Step 4: Unregister
        response = client.delete(f"/activities/{activity_name}/signup?email={new_email}")
        assert response.status_code == 200
        
        # Step 5: Verify removed from list
        activities = client.get("/activities").json()
        assert new_email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1

    def test_multiple_signups_and_unregisters(self, client):
        """Verify multiple participants can be added and removed."""
        activity_name = "Chess Club"
        emails = ["alice@mergington.edu", "bob@mergington.edu", "charlie@mergington.edu"]
        
        # Sign up all participants
        for email in emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all are in list
        activities = client.get("/activities").json()
        for email in emails:
            assert email in activities[activity_name]["participants"]
        
        assert len(activities[activity_name]["participants"]) == 5  # 2 original + 3 new
        
        # Unregister first participant
        response = client.delete(f"/activities/{activity_name}/signup?email=alice@mergington.edu")
        assert response.status_code == 200
        
        # Verify still has other new participants
        activities = client.get("/activities").json()
        assert "alice@mergington.edu" not in activities[activity_name]["participants"]
        assert "bob@mergington.edu" in activities[activity_name]["participants"]
        assert "charlie@mergington.edu" in activities[activity_name]["participants"]
