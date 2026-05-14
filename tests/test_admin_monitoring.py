import pytest
from fastapi.testclient import TestClient
from tests.conftest import SAMPLE_STUDENT


class TestAdminRoutes:
    def test_list_users_as_admin(self, client: TestClient, admin_headers, admin_user):
        response = client.get("/api/admin/users", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_users_as_student_forbidden(self, client: TestClient, student_headers):
        response = client.get("/api/admin/users", headers=student_headers)
        assert response.status_code == 403

    def test_get_user_by_id(self, client: TestClient, admin_headers, admin_user):
        response = client.get(f"/api/admin/users/{admin_user.id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == admin_user.id

    def test_get_nonexistent_user(self, client: TestClient, admin_headers):
        response = client.get("/api/admin/users/99999", headers=admin_headers)
        assert response.status_code == 404

    def test_toggle_user_active(self, client: TestClient, admin_headers, student_user):
        original_active = student_user.is_active
        response = client.put(f"/api/admin/users/{student_user.id}/toggle-active", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["is_active"] != original_active

    def test_cannot_toggle_own_account(self, client: TestClient, admin_headers, admin_user):
        response = client.put(f"/api/admin/users/{admin_user.id}/toggle-active", headers=admin_headers)
        assert response.status_code == 400

    def test_delete_user_as_admin(self, client: TestClient, admin_headers, student_user):
        response = client.delete(f"/api/admin/users/{student_user.id}", headers=admin_headers)
        assert response.status_code == 200

    def test_cannot_delete_own_account(self, client: TestClient, admin_headers, admin_user):
        response = client.delete(f"/api/admin/users/{admin_user.id}", headers=admin_headers)
        assert response.status_code == 400

    def test_get_all_audit_logs_as_admin(self, client: TestClient, admin_headers):
        response = client.get("/api/admin/audit-logs", headers=admin_headers)
        assert response.status_code == 200
        assert "logs" in response.json()

    def test_audit_log_created_on_student_create(self, client: TestClient, admin_headers):
        client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers)
        logs_response = client.get("/api/admin/audit-logs", headers=admin_headers)
        logs = logs_response.json()["logs"]
        create_logs = [l for l in logs if l["action"] == "CREATE"]
        assert len(create_logs) >= 1

    def test_audit_log_created_on_student_update(self, client: TestClient, admin_headers):
        created = client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers).json()
        client.put(f"/api/students/{created['id']}", json={"first_name": "Updated"}, headers=admin_headers)
        logs_response = client.get(f"/api/students/{created['id']}/audit-logs", headers=admin_headers)
        logs = logs_response.json()["logs"]
        update_logs = [l for l in logs if l["action"] == "UPDATE"]
        assert len(update_logs) >= 1


class TestMonitoringRoutes:
    def test_health_check_public(self, client: TestClient):
        response = client.get("/api/monitoring/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "cache" in data

    def test_metrics_as_admin(self, client: TestClient, admin_headers):
        response = client.get("/api/monitoring/metrics", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "error_rate" in data
        assert "cache" in data

    def test_metrics_as_student_forbidden(self, client: TestClient, student_headers):
        response = client.get("/api/monitoring/metrics", headers=student_headers)
        assert response.status_code == 403

    def test_stats_as_admin(self, client: TestClient, admin_headers):
        response = client.get("/api/monitoring/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_students" in data
        assert "gpa_stats" in data


class TestRoleBasedAccess:
    """Comprehensive role-based access control tests."""

    def test_student_cannot_create_student(self, client: TestClient, student_headers):
        response = client.post("/api/students", json=SAMPLE_STUDENT, headers=student_headers)
        assert response.status_code == 403

    def test_student_cannot_delete_student(self, client: TestClient, admin_headers, student_headers):
        created = client.post("/api/students", json=SAMPLE_STUDENT, headers=admin_headers).json()
        response = client.delete(f"/api/students/{created['id']}", headers=student_headers)
        assert response.status_code == 403

    def test_student_cannot_list_all_students(self, client: TestClient, student_headers):
        response = client.get("/api/students", headers=student_headers)
        assert response.status_code == 403

    def test_student_cannot_access_admin_routes(self, client: TestClient, student_headers):
        response = client.get("/api/admin/users", headers=student_headers)
        assert response.status_code == 403

    def test_student_cannot_view_metrics(self, client: TestClient, student_headers):
        response = client.get("/api/monitoring/metrics", headers=student_headers)
        assert response.status_code == 403

    def test_unauthenticated_cannot_access_protected(self, client: TestClient):
        endpoints = [
            ("GET", "/api/students"),
            ("POST", "/api/students"),
            ("GET", "/api/admin/users"),
            ("GET", "/api/monitoring/metrics"),
        ]
        for method, path in endpoints:
            response = client.request(method, path)
            assert response.status_code == 401, f"Expected 401 for {method} {path}, got {response.status_code}"
