from unittest.mock import AsyncMock

from app.utils.dependensy import get_case_service, get_verify_user


class TestGetCases:
    def test_get_cases_success(self, test_app, mock_user, mock_case):
        mock_case_service = AsyncMock()
        mock_case_service.get_cases.return_value = [mock_case]

        test_app.dependency_overrides[get_verify_user] = lambda: mock_user
        test_app.dependency_overrides[get_case_service] = lambda: mock_case_service

        from fastapi.testclient import TestClient

        with TestClient(test_app) as client:
            response = client.get("/api/cases")

        test_app.dependency_overrides.clear()

        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_case_service.get_cases.assert_awaited_once()

    def test_get_cases_not_found_when_empty(self, test_app, mock_user):
        mock_case_service = AsyncMock()
        mock_case_service.get_cases.return_value = []

        test_app.dependency_overrides[get_verify_user] = lambda: mock_user
        test_app.dependency_overrides[get_case_service] = lambda: mock_case_service

        from fastapi.testclient import TestClient

        with TestClient(test_app) as client:
            response = client.get("/api/cases")

        test_app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json()["detail"] == "Cases не найдены"

    def test_get_cases_not_found_when_no_user(self, test_app):
        mock_case_service = AsyncMock()

        test_app.dependency_overrides[get_verify_user] = lambda: None
        test_app.dependency_overrides[get_case_service] = lambda: mock_case_service

        from fastapi.testclient import TestClient

        with TestClient(test_app) as client:
            response = client.get("/api/cases")

        test_app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json()["detail"] == "Cases не найдены"
        mock_case_service.get_cases.assert_not_awaited()
