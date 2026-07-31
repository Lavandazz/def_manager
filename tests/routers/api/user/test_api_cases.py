from unittest.mock import AsyncMock

from app.utils.dependensy import get_case_service, get_verify_user


class TestGetUserCases:
    def test_get_user_cases_success(self, client_with_case_service, mock_case_service, mock_case):
        mock_case_service.get_user_cases.return_value = [mock_case]

        response = client_with_case_service.get("/api/cases/cases")

        assert response.status_code == 200
        assert "cases" in response.json()
        mock_case_service.get_user_cases.assert_awaited_once_with(user_id=1)

    def test_get_user_cases_not_found(self, client_with_case_service, mock_case_service):
        mock_case_service.get_user_cases.return_value = []

        response = client_with_case_service.get("/api/cases/cases")

        assert response.status_code == 404
        assert response.json()["detail"] == "Данных нет или нет зарегистрированных дел"


class TestAddCase:
    def test_add_case_success(self, test_app, mock_user, mock_case):
        mock_case_service = AsyncMock()
        mock_case_service.add_case.return_value = mock_case

        test_app.dependency_overrides[get_verify_user] = lambda: mock_user
        test_app.dependency_overrides[get_case_service] = lambda: mock_case_service

        from fastapi.testclient import TestClient

        with TestClient(test_app) as client:
            response = client.post(
                "/api/cases/cases/add_case",
                json={
                    "number_case": "A40-12345/2024",
                    "debtor": "ООО Тест",
                },
            )

        test_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Дело успешно добавлено"
        assert data["case"] is not None
        mock_case_service.add_case.assert_awaited_once()

    def test_add_case_user_not_found(self, test_app):
        mock_case_service = AsyncMock()

        test_app.dependency_overrides[get_verify_user] = lambda: None
        test_app.dependency_overrides[get_case_service] = lambda: mock_case_service

        from fastapi.testclient import TestClient

        with TestClient(test_app) as client:
            response = client.post(
                "/api/cases/cases/add_case",
                json={
                    "number_case": "A40-12345/2024",
                    "debtor": "ООО Тест",
                },
            )

        test_app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json()["detail"] == "Пользователь не найден"
        mock_case_service.add_case.assert_not_awaited()

    def test_add_case_validation_error(self, client_with_case_service):
        response = client_with_case_service.post(
            "/api/cases/cases/add_case",
            json={"number_case": "A40-12345/2024"},
        )

        assert response.status_code == 422
