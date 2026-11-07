from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from web_app.utils.auth.password_hasher import PasswordHasher
from web_app.utils.dependensy import get_case_service, get_optional_user


class TestMainPage:
    def test_main_page_anon(self, html_client_anon):
        response = html_client_anon.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Арбитражные дела" in response.text
        assert "Войти" in response.text

    def test_main_page_authenticated_with_cache(
        self, html_client_full, mock_user, cached_cases
    ):
        response = html_client_full.get("/")

        assert response.status_code == 200
        assert mock_user.username in response.text
        assert cached_cases[0]["number_case"] in response.text

    def test_main_page_authenticated_loads_from_db(
        self, html_app, mock_user, html_case, mock_case_service, patch_empty_cases_cache
    ):
        mock_case_service.get_user_cases.return_value = [html_case]
        html_app.dependency_overrides[get_optional_user] = lambda: mock_user
        html_app.dependency_overrides[get_case_service] = lambda: mock_case_service

        with patch(
            "web_app.routers.html.index.save_cases_to_cache",
            new_callable=AsyncMock,
        ):
            with TestClient(html_app) as client:
                response = client.get("/")

        html_app.dependency_overrides.clear()

        assert response.status_code == 200
        mock_case_service.get_user_cases.assert_awaited_once_with(user_id=mock_user.id)
        assert html_case.number_case in response.text


class TestLoginPage:
    def test_login_page_get(self, html_client_anon):
        response = html_client_anon.get("/login")

        assert response.status_code == 200
        assert "Вход в систему" in response.text
        assert 'name="email"' in response.text
        assert 'name="password"' in response.text


class TestLoginPost:
    def test_login_success(self, html_client_anon_services, mock_user_service, mock_user):
        password = "secret123"
        mock_user.hashed_password = PasswordHasher.hash_password(password)
        mock_user_service.get_user.return_value = mock_user

        with patch("web_app.routers.html.index.AuthTokenService") as mock_auth_cls:
            mock_auth_cls.return_value.create_token.return_value = "test-access-token"
            response = html_client_anon_services.post(
                "/login",
                data={"email": mock_user.email, "password": password},
                follow_redirects=False,
            )

        assert response.status_code == 303
        assert response.headers["location"] == "/"
        assert "access_token" in response.cookies
        assert response.cookies["access_token"] == "test-access-token"

    def test_login_invalid_credentials(
        self, html_client_anon_services, mock_user_service, mock_user
    ):
        mock_user.hashed_password = PasswordHasher.hash_password("correct")
        mock_user_service.get_user.return_value = mock_user

        response = html_client_anon_services.post(
            "/login",
            data={"email": mock_user.email, "password": "wrong"},
        )

        assert response.status_code == 200
        assert "Неверный email или пароль" in response.text

    def test_login_user_not_found(self, html_client_anon_services, mock_user_service):
        mock_user_service.get_user.return_value = None

        response = html_client_anon_services.post(
            "/login",
            data={"email": "missing@example.com", "password": "secret123"},
        )

        assert response.status_code == 200
        assert "Неверный email или пароль" in response.text

    def test_login_missing_fields(self, html_client_anon_services):
        response = html_client_anon_services.post("/login", data={})

        assert response.status_code == 422


class TestLogout:
    def test_logout(self, html_client):
        response = html_client.get("/logout", follow_redirects=False)

        assert response.status_code in (302, 303, 307)
        assert "/login" in response.headers["location"]
