"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_required_activities(self, client):
        """Test that activities include expected activities"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in activities

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for activity_data in activities.values():
            for field in required_fields:
                assert field in activity_data


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_returns_message(self, client):
        """Test that signup returns a message"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert "message" in response.json()

    def test_signup_activity_not_found(self, client):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_student(self, client):
        """Test that duplicate signup fails"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Drama%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Drama%20Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_updates_participant_list(self, client):
        """Test that signup actually adds participant to activity"""
        email = "verify@mergington.edu"
        
        # Get initial participant count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Tennis Club"]["participants"])
        
        # Sign up
        client.post(f"/activities/Tennis%20Club/signup?email={email}")
        
        # Verify participant was added
        response2 = client.get("/activities")
        new_count = len(response2.json()["Tennis Club"]["participants"])
        assert new_count == initial_count + 1
        assert email in response2.json()["Tennis Club"]["participants"]


class TestUnregisterEndpoint:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful(self, client):
        """Test successful unregister from an activity"""
        email = "tounregister@mergington.edu"
        
        # First sign up
        client.post(f"/activities/Basketball%20Team/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Basketball%20Team/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_student_not_signed_up(self, client):
        """Test unregister fails when student is not signed up"""
        response = client.post(
            "/activities/Robotics%20Team/unregister?email=notsignedup@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant from activity"""
        email = "removeme@mergington.edu"
        
        # Sign up
        signup_response = client.post(f"/activities/Art%20Studio/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Get count with participant
        response1 = client.get("/activities")
        count_with = len(response1.json()["Art Studio"]["participants"])
        
        # Unregister
        client.post(f"/activities/Art%20Studio/unregister?email={email}")
        
        # Verify participant was removed
        response2 = client.get("/activities")
        count_without = len(response2.json()["Art Studio"]["participants"])
        assert count_without == count_with - 1
        assert email not in response2.json()["Art Studio"]["participants"]


class TestRootEndpoint:
    """Tests for the GET / endpoint"""

    def test_root_redirects(self, client):
        """Test that root endpoint redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307


class TestParticipantCapacity:
    """Tests for participant capacity limits"""

    def test_activity_tracks_max_participants(self, client):
        """Test that activities have a max_participants field"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_data in activities.values():
            assert "max_participants" in activity_data
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0

    def test_spots_left_calculation(self, client):
        """Test that we can calculate remaining spots correctly"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_data in activities.values():
            spots_left = activity_data["max_participants"] - len(activity_data["participants"])
            assert spots_left >= 0
