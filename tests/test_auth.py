import pytest
from fastapi.testclient import TestClient


class TestRegistration:
    def test_register_success(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "email": "new@test.com",
            "username": "newuser",
            "password": "password123",
            "role": "student"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@test.com"
        assert data["username"] == "newuser"
        assert data["role"] == "student"
        assert "hashed_password" not in data

    def test_register_admin(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "email": "admin@test.com",
            "username": "adminuser",
            "password": "admin123",
            "role": "admin"
        })
        assert response.status_code == 201
        assert response.json()["role"] == "admin"

    def test_register_duplicate_email(self, client: TestClient, admin_user):
        response = client.post("/api/auth/register", json={
            "email": "admin@test.com",
            "username": "differentuser",
            "password": "password123",
        })
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_duplicate_username(self, client: TestClient, admin_user):
        response = client.post("/api/auth/register", json={
            "email": "different@test.com",
            "username": "adminuser",
            "password": "password123",
        })
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    def test_register_invalid_email(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "email": "not-an-email",
            "username": "user",
            "password": "password123",
        })
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "email": "test@test.com",
            "username": "user",
            "password": "abc",
        })
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client: TestClient, admin_user):
        response = client.post("/api/auth/login", json={
            "username": "adminuser",
            "password": "adminpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, admin_user):
        response = client.post("/api/auth/login", json={
            "username": "adminuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "password123"
        })
        assert response.status_code == 401

    def test_login_inactive_user(self, client: TestClient, db, admin_user):
        admin_user.is_active = False
        db.commit()
        response = client.post("/api/auth/login", json={
            "username": "adminuser",
            "password": "adminpass123"
        })
        assert response.status_code == 403


class TestTokenValidation:
    def test_get_me_valid_token(self, client: TestClient, admin_headers):
        response = client.get("/api/auth/me", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["username"] == "adminuser"

    def test_get_me_no_token(self, client: TestClient):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client: TestClient):
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert response.status_code == 401

    def test_logout(self, client: TestClient, admin_headers):
        response = client.post("/api/auth/logout", headers=admin_headers)
        assert response.status_code == 200
        assert "message" in response.json()
