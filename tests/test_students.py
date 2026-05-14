import pytest
from fastapi.testclient import TestClient
from tests.conftest import SAMPLE_STUDENT


class TestCreateStudent:
    def test_create_student_as_admin(self, client: TestClient, admin_headers):
        response = client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["student_id"] == "STU001"
        assert data["first_name"] == "John"
        assert data["gpa"] == 3.5

    def test_create_student_as_student_forbidden(self, client: TestClient, student_headers):
        response = client.post("/api/students", json=SAMPLE_STUDENT, headers=student_headers)
        assert response.status_code == 403

    def test_create_student_unauthenticated(self, client: TestClient):
        response = client.post("/api/students", json=SAMPLE_STUDENT)
        assert response.status_code == 401

    def test_create_student_duplicate_id(self, client: TestClient, admin_headers):
        client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers)
        response = client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers)
        assert response.status_code == 400
        assert "Student ID already exists" in response.json()["detail"]

    def test_create_student_duplicate_email(self, client: TestClient, admin_headers):
        client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers)
        duplicate = {**SAMPLE_STUDENT, "student_id": "STU002"}
        response = client.post("/api/students", json=duplicate, headers=admin_headers)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_create_student_invalid_gpa(self, client: TestClient, admin_headers):
        invalid = {**SAMPLE_STUDENT, "gpa": 5.0}
        response = client.post("/api/students", json=invalid, headers=admin_headers)
        assert response.status_code == 422

    def test_create_student_invalid_year(self, client: TestClient, admin_headers):
        invalid = {**SAMPLE_STUDENT, "year": 10}
        response = client.post("/api/students", json=invalid, headers=admin_headers)
        assert response.status_code == 422

    def test_create_student_missing_required_field(self, client: TestClient, admin_headers):
        incomplete = {k: v for k, v in SAMPLE_STUDENT.items() if k != "department"}
        response = client.post("/api/students", json=incomplete, headers=admin_headers)
        assert response.status_code == 422


class TestGetStudents:
    def test_list_students_as_admin(self, client: TestClient, admin_headers):
        client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers)
        response = client.get("/api/students", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        assert data["total"] >= 1
        assert "page" in data

    def test_list_students_as_student_forbidden(self, client: TestClient, student_headers):
        response = client.get("/api/students", headers=student_headers)
        assert response.status_code == 403

    def test_list_students_pagination(self, client: TestClient, admin_headers):
        # Create 3 students
        for i in range(1, 4):
            s = {**SAMPLE_STUDENT, "student_id": f"STU00{i}", "email": f"student{i}@u.edu"}
            client.post("/api/students", json=s, headers=admin_headers)
        response = client.get("/api/students?page=1&page_size=2", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["students"]) <= 2
        assert data["page"] == 1

    def test_filter_by_department(self, client: TestClient, admin_headers):
        client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers)
        response = client.get("/api/students?department=Computer+Science", headers=admin_headers)
        assert response.status_code == 200

    def test_filter_by_gpa(self, client: TestClient, admin_headers):
        client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers)
        response = client.get("/api/students?min_gpa=3.0&max_gpa=4.0", headers=admin_headers)
        assert response.status_code == 200
        for s in response.json()["students"]:
            assert 3.0 <= s["gpa"] <= 4.0

    def test_search_student(self, client: TestClient, admin_headers):
        client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers)
        response = client.get("/api/students?search=John", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    def test_get_student_by_id_as_admin(self, client: TestClient, admin_headers):
        created = client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers).json()
        response = client.get(f"/api/students/{created['id']}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_nonexistent_student(self, client: TestClient, admin_headers):
        response = client.get("/api/students/99999", headers=admin_headers)
        assert response.status_code == 404

    def test_student_cannot_access_other_student(self, client: TestClient, admin_headers, student_headers):
        created = client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers).json()
        response = client.get(f"/api/students/{created['id']}", headers=student_headers)
        assert response.status_code == 403


class TestUpdateStudent:
    def test_admin_update_student(self, client: TestClient, admin_headers):
        created = client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers).json()
        response = client.put(
            f"/api/students/{created['id']}",
            json={"first_name": "Jane", "gpa": 3.8},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["gpa"] == 3.8

    def test_student_cannot_admin_update(self, client: TestClient, admin_headers, student_headers):
        created = client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers).json()
        response = client.put(
            f"/api/students/{created['id']}",
            json={"first_name": "Jane"},
            headers=student_headers,
        )
        assert response.status_code == 403

    def test_update_nonexistent_student(self, client: TestClient, admin_headers):
        response = client.put("/api/students/99999", json={"first_name": "Test"}, headers=admin_headers)
        assert response.status_code == 404

    def test_update_invalid_gpa(self, client: TestClient, admin_headers):
        created = client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers).json()
        response = client.put(
            f"/api/students/{created['id']}",
            json={"gpa": -1.0},
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestDeleteStudent:
    def test_admin_delete_student(self, client: TestClient, admin_headers):
        created = client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers).json()
        response = client.delete(f"/api/students/{created['id']}", headers=admin_headers)
        assert response.status_code == 200
        # Verify deleted
        get_response = client.get(f"/api/students/{created['id']}", headers=admin_headers)
        assert get_response.status_code == 404

    def test_student_cannot_delete(self, client: TestClient, admin_headers, student_headers):
        created = client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers).json()
        response = client.delete(f"/api/students/{created['id']}", headers=student_headers)
        assert response.status_code == 403

    def test_delete_nonexistent_student(self, client: TestClient, admin_headers):
        response = client.delete("/api/students/99999", headers=admin_headers)
        assert response.status_code == 404


class TestMyProfile:
    def test_student_get_own_profile(self, client: TestClient, admin_headers, student_user, student_headers, db):
        # Link student record to student user
        student_data = {**SAMPLE_STUDENT, "user_id": student_user.id}
        created = client.post("/api/students", json=student_data, headers=admin_headers).json()
        response = client.get("/api/students/me", headers=student_headers)
        assert response.status_code == 200

    def test_admin_get_me_returns_error(self, client: TestClient, admin_headers):
        response = client.get("/api/students/me", headers=admin_headers)
        assert response.status_code == 400
