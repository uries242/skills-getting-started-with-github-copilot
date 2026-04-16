"""
Comprehensive test suite for the Mergington High School Activities API.

Tests cover:
- GET /activities endpoint
- POST /activities/{activity_name}/signup endpoint
- DELETE /activities/{activity_name}/unregister endpoint

Tests validate happy paths, error cases, edge cases, and response validation.
"""

import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, fresh_activities):
        """Test that the endpoint returns all activities with correct structure."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        
        # Verify all activities are returned
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
        
    def test_get_activities_structure(self, client, fresh_activities):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)
            
    def test_get_activities_participant_counts(self, client, fresh_activities):
        """Test that participant counts match expected values."""
        response = client.get("/activities")
        activities = response.json()
        
        # Verify specific participant counts
        assert len(activities["Chess Club"]["participants"]) == 2
        assert len(activities["Programming Class"]["participants"]) == 2
        assert len(activities["Basketball Team"]["participants"]) == 1


class TestSignupHappyPath:
    """Tests for successful signup scenarios."""

    def test_signup_successful(self, client, fresh_activities):
        """Test successful signup adds participant and returns success message."""
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            headers={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
    def test_signup_adds_participant_to_list(self, client, fresh_activities):
        """Test that signup adds the participant to the activity's participant list."""
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Signup
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity_name]["participants"]
        
    def test_signup_reduces_availability(self, client, fresh_activities):
        """Test that signup reduces available spots."""
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_participants = len(response.json()[activity_name]["participants"])
        
        # Signup
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify participant count increased
        response = client.get("/activities")
        new_participants = len(response.json()[activity_name]["participants"])
        assert new_participants == initial_participants + 1
        
    def test_signup_multiple_different_activities(self, client, fresh_activities):
        """Test that a student can signup for multiple different activities."""
        email = "multistudent@mergington.edu"
        
        # Signup for Chess Club
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Signup for Programming Class
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify student is in both
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestSignupErrorCases:
    """Tests for signup error scenarios."""

    def test_signup_activity_not_found(self, client, fresh_activities):
        """Test error when signup for non-existent activity."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
        
    def test_signup_already_signed_up(self, client, fresh_activities):
        """Test error when student already signed up for activity."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]
        
    def test_signup_activity_at_max_capacity(self, client, fresh_activities):
        """Test error when activity is at maximum capacity."""
        activity_name = "Basketball Team"  # 1 of 15 capacity
        
        # Fill the activity to capacity
        for i in range(14):
            email = f"student{i}@mergington.edu"
            client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Try to signup when at capacity
        response = client.post(
            f"/activities/{activity_name}/signup?email=overcapacity@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "maximum capacity" in data["detail"]
        
    def test_signup_missing_email_parameter(self, client, fresh_activities):
        """Test error when email parameter is missing."""
        response = client.post("/activities/Chess Club/signup")
        
        assert response.status_code == 422
        
    def test_signup_missing_activity_name(self, client, fresh_activities):
        """Test error when activity name is missing in URL."""
        response = client.post("/activities//signup?email=student@mergington.edu")
        
        assert response.status_code != 200  # Should fail with bad URL
        
class TestUnregisterHappyPath:
    """Tests for successful unregister scenarios."""

    def test_unregister_successful(self, client, fresh_activities):
        """Test successful unregister removes participant and returns success message."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
    def test_unregister_removes_participant(self, client, fresh_activities):
        """Test that unregister removes the participant from the activity."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Unregister
        client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity_name]["participants"]
        
    def test_unregister_increases_availability(self, client, fresh_activities):
        """Test that unregister increases available spots."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_participants = len(response.json()[activity_name]["participants"])
        
        # Unregister
        client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        # Verify participant count decreased
        response = client.get("/activities")
        new_participants = len(response.json()[activity_name]["participants"])
        assert new_participants == initial_participants - 1
        
    def test_unregister_then_signup_again(self, client, fresh_activities):
        """Test that a student can unregister and then signup again."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Unregister
        response1 = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response1.status_code == 200
        
        # Signup again
        response2 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify student is back in activity
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity_name]["participants"]


class TestUnregisterErrorCases:
    """Tests for unregister error scenarios."""

    def test_unregister_activity_not_found(self, client, fresh_activities):
        """Test error when unregister from non-existent activity."""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
        
    def test_unregister_student_not_enrolled(self, client, fresh_activities):
        """Test error when student is not enrolled in activity."""
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"]
        
    def test_unregister_missing_email_parameter(self, client, fresh_activities):
        """Test error when email parameter is missing."""
        response = client.delete("/activities/Chess Club/unregister")
        
        assert response.status_code == 422
        
    def test_unregister_missing_activity_name(self, client, fresh_activities):
        """Test error when activity name is missing in URL."""
        response = client.delete("/activities//unregister?email=student@mergington.edu")
        
        assert response.status_code != 200  # Should fail with bad URL


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_root_endpoint_redirects(self, client, fresh_activities):
        """Test that root endpoint redirects to static files."""
        response = client.get("/", follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_activity_with_special_characters_in_name(self, client, fresh_activities):
        """Test signup/unregister with activity names containing special characters."""
        activity_name = "Chess Club"  # Already exists, has no special chars
        email = "test@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
    def test_email_with_special_characters(self, client, fresh_activities):
        """Test signup with email containing special characters."""
        activity_name = "Chess Club"
        email = "test+tag@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
    def test_case_sensitive_activity_names(self, client, fresh_activities):
        """Test that activity names are case-sensitive."""
        response = client.post("/activities/chess club/signup?email=test@mergington.edu")
        
        # Should fail because "chess club" != "Chess Club"
        assert response.status_code == 404
        
    def test_concurrent_operations(self, client, fresh_activities):
        """Test sequential operations to ensure consistency."""
        activity_name = "Chess Club"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Signup first student
        client.post(f"/activities/{activity_name}/signup?email={email1}")
        
        # Signup second student
        client.post(f"/activities/{activity_name}/signup?email={email2}")
        
        # Verify both are in the activity
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants
        
        # Unregister first student
        client.delete(f"/activities/{activity_name}/unregister?email={email1}")
        
        # Verify only second student remains
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert email1 not in participants
        assert email2 in participants
