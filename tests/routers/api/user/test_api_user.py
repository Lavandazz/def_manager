from unittest.mock import AsyncMock, patch

from app.utils.auth.password_hasher import PasswordHasher


class TestGetProfile:
    def test_get_profile_success(self, client, mock_user):
        response = client.get("/api/user/profile")

        assert response.status_code == 200
        assert response.json() == {
            "username": mock_user.username,
            "email": mock_user.email,
            "telegram_id": mock_user.telegram_id,
        }

    def test_get_profile_not_found(self, client_without_user):
        response = client_without_user.get("/api/user/profile")

        assert response.status_code == 404
        assert response.json()["detail"] == "Пользователь не найден"


class TestRegisterUser:
    def test_register_success(self, client_with_user_service, mock_user_service):
        mock_user_service.get_user.return_value = None

        response = client_with_user_service.post(
            "/api/user/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "secret123",
                "second_password": "secret123",
                "telegram_id": 999,
            },
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Пользователь зарегистрирован"
        assert response.json()["user"] == "newuser"
        mock_user_service.create_user.assert_awaited_once()

    def test_register_passwords_mismatch(self, client_with_user_service):
        response = client_with_user_service.post(
            "/api/user/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "secret123",
                "second_password": "other123",
                "telegram_id": 999,
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Пароли не совпадают"

    def test_register_user_already_exists(self, client_with_user_service, mock_user_service, mock_user):
        mock_user_service.get_user.return_value = mock_user

        response = client_with_user_service.post(
            "/api/user/register",
            json={
                "username": "newuser",
                "email": "test@example.com",
                "password": "secret123",
                "second_password": "secret123",
                "telegram_id": 999,
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Пользователь уже существует"

    def test_register_server_error(self, client_with_user_service, mock_user_service):
        mock_user_service.get_user.side_effect = RuntimeError("db error")

        response = client_with_user_service.post(
            "/api/user/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "secret123",
                "second_password": "secret123",
                "telegram_id": 999,
            },
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Ошибка сервера"


class TestLogin:
    def test_login_success(self, client_with_user_service, mock_user_service, mock_user):
        password = "secret123"
        mock_user.hashed_password = PasswordHasher.hash_password(password)
        mock_user_service.get_user.return_value = mock_user

        with patch("app.routers.api.user.api_user.AuthTokenService") as mock_auth_cls:
            mock_auth = mock_auth_cls.return_value
            mock_auth.create_token.side_effect = ["access-token", "refresh-token"]

            response = client_with_user_service.post(
                "/api/user/login",
                json={
                    "email": mock_user.email,
                    "password": password,
                    "telegram_id": mock_user.telegram_id,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Успешная авторизация"
        assert data["user"] == mock_user.username
        assert data["email"] == mock_user.email
        assert data["access_token"] == "access-token"
        assert data["token_type"] == "bearer"

    def test_login_empty_fields(self, client_with_user_service):
        response = client_with_user_service.post(
            "/api/user/login",
            json={"email": "test@example.com", "password": "", "telegram_id": 1},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Заполните все поля"

    def test_login_invalid_email_format(self, client_with_user_service):
        response = client_with_user_service.post(
            "/api/user/login",
            json={"email": "", "password": "secret123", "telegram_id": 1},
        )

        assert response.status_code == 422

    def test_login_invalid_credentials(self, client_with_user_service, mock_user_service, mock_user):
        mock_user.hashed_password = PasswordHasher.hash_password("correct-password")
        mock_user_service.get_user.return_value = mock_user

        response = client_with_user_service.post(
            "/api/user/login",
            json={
                "email": mock_user.email,
                "password": "wrong-password",
                "telegram_id": mock_user.telegram_id,
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Неверно введены логин или пароль"

    def test_login_user_not_found(self, client_with_user_service, mock_user_service):
        mock_user_service.get_user.return_value = None

        response = client_with_user_service.post(
            "/api/user/login",
            json={
                "email": "missing@example.com",
                "password": "secret123",
                "telegram_id": 1,
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Неверно введены логин или пароль"


class TestLogout:
    def test_logout_success(self, client_with_token_service, mock_token_service):
        response = client_with_token_service.post(
            "/api/user/logout",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Успешный выход из системы"
        mock_token_service.add_token.assert_awaited_once_with(token="test-token")

    def test_logout_missing_token(self, client_with_token_service):
        response = client_with_token_service.post("/api/user/logout")

        assert response.status_code == 401
