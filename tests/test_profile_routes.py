"""Integration tests for profile routes."""


class TestGetProfile:
    """Profile retrieval tests."""

    def test_get_profile(self, authenticated_client, test_user):
        """Test getting user profile."""
        response = authenticated_client.get("/api/v1/profile/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_profile_requires_auth(self, client, temp_db):
        """Test that getting profile requires auth."""
        response = client.get("/api/v1/profile/")
        assert response.status_code == 401


class TestUpdateProfile:
    """Profile update tests."""

    def test_update_profile(self, authenticated_client, test_user):
        """Test updating profile fields."""
        response = authenticated_client.put(
            "/api/v1/profile/",
            json={
                "first_name": "Updated",
                "last_name": "Name",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"

    def test_update_profile_gym(self, authenticated_client, test_user):
        """Test updating gym field."""
        response = authenticated_client.put(
            "/api/v1/profile/",
            json={"default_gym": "New Gym"},
        )
        assert response.status_code == 200

    def test_update_profile_city(self, authenticated_client, test_user):
        """Test partial profile update (only city)."""
        response = authenticated_client.put(
            "/api/v1/profile/",
            json={"city": "Melbourne"},
        )
        assert response.status_code == 200


class TestOnboardingStatus:
    """Onboarding status tests."""

    def test_get_onboarding_status(self, authenticated_client, test_user):
        """Test getting onboarding status."""
        response = authenticated_client.get("/api/v1/profile/onboarding-status")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_onboarding_requires_auth(self, client, temp_db):
        """Test that onboarding status requires auth."""
        response = client.get("/api/v1/profile/onboarding-status")
        assert response.status_code == 401


class TestProfilePhoto:
    """Profile photo tests."""

    def test_upload_photo_no_file(self, authenticated_client, test_user):
        """Test uploading photo without file data fails."""
        response = authenticated_client.post("/api/v1/profile/photo")
        assert response.status_code == 422

    def test_delete_photo_no_photo(self, authenticated_client, test_user):
        """Test deleting photo when none exists."""
        response = authenticated_client.delete("/api/v1/profile/photo")
        # Should succeed gracefully or return appropriate error
        assert response.status_code in (200, 404)
