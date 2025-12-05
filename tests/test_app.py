import pytest


class TestRoot:
    def test_root_redirect(self, client):
        """Test that root redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    def test_get_all_activities(self, client, reset_activities):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activities_have_required_fields(self, client, reset_activities):
        """Test that activities have required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_activities_participants_list(self, client, reset_activities):
        """Test that participants are correctly listed"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    def test_successful_signup(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Tennis Club/signup?email=john@test.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "john@test.edu" in data["message"]
        assert "Tennis Club" in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant"""
        # Signup
        response = client.post(
            "/activities/Tennis Club/signup?email=newstudent@test.edu"
        )
        assert response.status_code == 200
        
        # Verify in activities list
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@test.edu" in data["Tennis Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@test.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_participant(self, client, reset_activities):
        """Test signup for activity when already registered"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_students(self, client, reset_activities):
        """Test that multiple students can sign up for same activity"""
        client.post("/activities/Tennis Club/signup?email=student1@test.edu")
        client.post("/activities/Tennis Club/signup?email=student2@test.edu")
        
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Tennis Club"]["participants"]) == 2
        assert "student1@test.edu" in data["Tennis Club"]["participants"]
        assert "student2@test.edu" in data["Tennis Club"]["participants"]


class TestUnregisterFromActivity:
    def test_successful_unregister(self, client, reset_activities):
        """Test successful unregister from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        # Unregister
        response = client.delete(
            "/activities/Chess Club/unregister?email=daniel@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify removed from activities list
        response = client.get("/activities")
        data = response.json()
        assert "daniel@mergington.edu" not in data["Chess Club"]["participants"]
        assert len(data["Chess Club"]["participants"]) == 1
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@test.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered_student(self, client, reset_activities):
        """Test unregister for student not in the activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@test.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_from_empty_activity(self, client, reset_activities):
        """Test unregister from activity with no participants"""
        response = client.delete(
            "/activities/Tennis Club/unregister?email=anyone@test.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]


class TestIntegration:
    def test_signup_then_unregister(self, client, reset_activities):
        """Test signup followed by unregister"""
        email = "integration@test.edu"
        
        # Signup
        response = client.post(f"/activities/Tennis Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()["Tennis Club"]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/Tennis Club/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify unregistered
        response = client.get("/activities")
        assert email not in response.json()["Tennis Club"]["participants"]
    
    def test_full_workflow(self, client, reset_activities):
        """Test a complete workflow: signup, view, unregister"""
        email = "workflow@test.edu"
        activity = "Programming Class"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify count increased
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        
        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify count decreased back
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count
