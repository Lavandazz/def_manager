from unittest.mock import AsyncMock, MagicMock, patch

from shared.utils.exceptions import VerificationCodeAlreadySent
from web_app.utils.auth.password_hasher import PasswordHasher


def _sync_password_setup(mock_user_service, value: bool = False) -> None:
    """needs_password_setup — синхронный метод, AsyncMock тут ломает ветки."""
    mock_user_service.needs_password_setup = MagicMock(return_value=value)


class TestGetProfile:
    def test_profile_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.get("/user/profile")

        assert response.status_code == 200
        assert "Пользователь не авторизован" in response.text

    def test_profile_success(self, html_client_full, mock_user_service, mock_user):
        mock_user_service.get_user_profile.return_value = mock_user

        response = html_client_full.get("/user/profile")

        assert response.status_code == 200
        assert "Профиль пользователя" in response.text
        assert mock_user.username in response.text
        mock_user_service.get_user_profile.assert_awaited_once_with(user_id=mock_user.id)


class TestEditProfileForm:
    def test_edit_form_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.get("/user/profile/edit")

        assert response.status_code == 200
        assert "Пользователь не авторизован" in response.text

    def test_edit_form_success(self, html_client_full, mock_user_service, mock_user):
        mock_user.hashed_password = PasswordHasher.hash_password("secret123")
        mock_user_service.get_user_profile.return_value = mock_user

        response = html_client_full.get("/user/profile/edit")

        assert response.status_code == 200
        assert "Редактирование профиля" in response.text
        assert "Данные арбитражного управляющего" in response.text
        mock_user_service.get_user_profile.assert_awaited_once_with(user_id=mock_user.id)

    def test_edit_form_redirects_when_password_needed(self, html_client_full, mock_user):
        with patch(
            "web_app.routers.html.user.PasswordHasher.compare_password",
            return_value=True,
        ):
            response = html_client_full.get("/user/profile/edit", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/user/profile/password"


class TestUpdateProfile:
    def test_update_unauthorized(self, html_client_anon_services, mock_user):
        response = html_client_anon_services.post(
            "/user/profile/edit",
            data={
                "username": mock_user.username,
                "email": mock_user.email,
                "telegram_id": "",
                "password": "secret",
            },
        )

        assert response.status_code == 401
        assert "Не авторизован" in response.text

    def test_update_empty_password(self, html_client_full, mock_user_service, mock_user):
        mock_user.hashed_password = PasswordHasher.hash_password("correct")
        mock_user_service.get_user_profile.return_value = mock_user

        response = html_client_full.post(
            "/user/profile/edit",
            data={
                "username": mock_user.username,
                "email": "new@example.com",
                "password": "",
            },
        )

        assert response.status_code == 400
        assert "Введите пароль для подтверждения изменений" in response.text
        mock_user_service.update_profile.assert_not_awaited()

    def test_update_wrong_password(self, html_client_full, mock_user_service, mock_user):
        mock_user.hashed_password = PasswordHasher.hash_password("correct")
        mock_user_service.get_user_profile.return_value = mock_user

        response = html_client_full.post(
            "/user/profile/edit",
            data={
                "username": mock_user.username,
                "email": "new@example.com",
                "telegram_id": "0",
                "password": "wrong",
            },
        )

        assert response.status_code == 400
        assert "Неверный пароль" in response.text
        mock_user_service.update_profile.assert_not_awaited()

    def test_update_success(self, html_client_full, mock_user_service, mock_user):
        password = "secret123"
        mock_user.hashed_password = PasswordHasher.hash_password(password)
        mock_user_service.get_user_profile.return_value = mock_user
        mock_user_service.update_profile.return_value = mock_user

        response = html_client_full.post(
            "/user/profile/edit",
            data={
                "username": mock_user.username,
                "email": "new@example.com",
                "telegram_id": "999",
                "inn": "123456789012",
                "snils": "123-456-789 00",
                "reg_num": "REG-1",
                "reg_date": "2020-01-15",
                "date_begin": "2021-02-01",
                "password": password,
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/user/profile"
        mock_user_service.update_profile.assert_awaited_once()
        saved = mock_user_service.update_profile.await_args.args[1]
        assert saved.email == "new@example.com"
        assert saved.username == mock_user.username
        assert saved.telegram_id == 999
        assert saved.inn == "123456789012"
        assert saved.snils == "123-456-789 00"
        assert saved.reg_num == "REG-1"
        assert saved.reg_date.isoformat() == "2020-01-15"
        assert saved.date_begin.isoformat() == "2021-02-01"

    def test_update_with_mail_address(
        self, html_client_full, mock_user_service, mock_mail_service, mock_user
    ):
        password = "secret123"
        mock_user.hashed_password = PasswordHasher.hash_password(password)
        mock_user_service.get_user_profile.return_value = mock_user
        mock_user_service.update_profile.return_value = mock_user
        mock_mail_service.create_mail_address.return_value = AsyncMock(id=42)

        response = html_client_full.post(
            "/user/profile/edit",
            data={
                "username": mock_user.username,
                "email": mock_user.email,
                "mail_index": "123456",
                "region_name": "Московская",
                "city": "Москва",
                "street": "Тверская",
                "house": "1",
                "building": "2",
                "password": password,
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        mock_mail_service.create_mail_address.assert_awaited_once()
        saved = mock_user_service.update_profile.await_args.args[1]
        assert saved.mail_address_id == 42


class TestPasswordForm:
    def test_password_form_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.get(
            "/user/profile/password", follow_redirects=False
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_password_form_success(self, html_client_full, mock_user_service):
        _sync_password_setup(mock_user_service, False)

        response = html_client_full.get("/user/profile/password")

        assert response.status_code == 200
        assert "Смена пароля" in response.text


class TestUpdatePassword:
    def test_update_password_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.post(
            "/user/profile/password",
            data={
                "new_password": "newpass12",
                "confirm_password": "newpass12",
                "current_password": "old",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_update_password_too_short(self, html_client_full, mock_user_service):
        _sync_password_setup(mock_user_service, False)

        response = html_client_full.post(
            "/user/profile/password",
            data={
                "new_password": "short",
                "confirm_password": "short",
                "current_password": "oldpass12",
            },
        )

        assert response.status_code == 400
        assert "не короче" in response.text

    def test_update_password_mismatch(self, html_client_full, mock_user_service):
        _sync_password_setup(mock_user_service, False)

        response = html_client_full.post(
            "/user/profile/password",
            data={
                "new_password": "newpass12",
                "confirm_password": "otherpass",
                "current_password": "oldpass12",
            },
        )

        assert response.status_code == 400
        assert "не совпадают" in response.text

    def test_change_password_missing_current(self, html_client_full, mock_user_service):
        _sync_password_setup(mock_user_service, False)

        response = html_client_full.post(
            "/user/profile/password",
            data={
                "new_password": "newpass12",
                "confirm_password": "newpass12",
            },
        )

        assert response.status_code == 400
        assert "Введите текущий пароль" in response.text

    def test_change_password_wrong_current(self, html_client_full, mock_user_service):
        _sync_password_setup(mock_user_service, False)
        mock_user_service.change_password.return_value = False

        response = html_client_full.post(
            "/user/profile/password",
            data={
                "new_password": "newpass12",
                "confirm_password": "newpass12",
                "current_password": "wrong",
            },
        )

        assert response.status_code == 400
        assert "Неверный текущий пароль" in response.text

    def test_change_password_success(self, html_client_full, mock_user_service):
        _sync_password_setup(mock_user_service, False)
        mock_user_service.change_password.return_value = True

        response = html_client_full.post(
            "/user/profile/password",
            data={
                "new_password": "newpass12",
                "confirm_password": "newpass12",
                "current_password": "oldpass12",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "/user/profile" in response.headers["location"]
        assert "password_updated=1" in response.headers["location"]

    def test_set_password_first_time(self, html_client_full, mock_user_service):
        _sync_password_setup(mock_user_service, True)
        mock_user_service.set_password.return_value = True

        response = html_client_full.post(
            "/user/profile/password",
            data={
                "new_password": "newpass12",
                "confirm_password": "newpass12",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        mock_user_service.set_password.assert_awaited_once()


class TestRegister:
    def test_register_form_get(self, html_client_anon):
        response = html_client_anon.get("/user/register")

        assert response.status_code == 200
        assert "Регистрация" in response.text

    def test_register_passwords_mismatch(self, html_client_anon_services):
        response = html_client_anon_services.post(
            "/user/register",
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password": "secret123",
                "second_password": "other123",
                "telegram_id": "",
            },
        )

        assert response.status_code == 200
        assert "Пароли не совпадают" in response.text

    def test_register_user_exists(
        self, html_client_anon_services, mock_user_service, mock_user
    ):
        mock_user_service.get_user.return_value = mock_user

        response = html_client_anon_services.post(
            "/user/register",
            data={
                "username": "newuser",
                "email": mock_user.email,
                "password": "secret123",
                "second_password": "secret123",
                "telegram_id": "",
            },
        )

        assert response.status_code == 200
        assert "Пользователь уже существует" in response.text

    def test_register_success_shows_verify(
        self, html_client_anon_services, mock_user_service, mock_redis_service
    ):
        mock_user_service.get_user.return_value = None
        mock_redis_service.generate_and_save_verification_code.return_value = "123456"
        mock_redis_service.redis_client.exists.return_value = 1

        with patch("web_app.routers.html.user.send_verification_email") as mock_task:
            mock_task.delay = lambda *a, **k: None
            response = html_client_anon_services.post(
                "/user/register",
                data={
                    "username": "newuser",
                    "email": "new@example.com",
                    "password": "secret123",
                    "second_password": "secret123",
                    "telegram_id": "",
                },
            )

        assert response.status_code == 200
        assert "Подтверждение почты" in response.text
        assert "new@example.com" in response.text

    def test_register_code_already_sent(
        self, html_client_anon_services, mock_user_service, mock_redis_service
    ):
        mock_user_service.get_user.return_value = None
        mock_redis_service.generate_and_save_verification_code.side_effect = (
            VerificationCodeAlreadySent("Код уже отправлен")
        )

        response = html_client_anon_services.post(
            "/user/register",
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password": "secret123",
                "second_password": "secret123",
                "telegram_id": "",
            },
        )

        assert response.status_code == 200
        assert "Код уже отправлен" in response.text

    def test_register_server_error(self, html_client_anon_services, mock_user_service):
        mock_user_service.get_user.side_effect = RuntimeError("db error")

        response = html_client_anon_services.post(
            "/user/register",
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password": "secret123",
                "second_password": "secret123",
                "telegram_id": "",
            },
        )

        assert response.status_code == 200
        assert "Ошибка сервера" in response.text


class TestVerify:
    def test_verify_code_not_found(
        self, html_client_anon_services, mock_redis_service
    ):
        mock_redis_service.get_verification_data.return_value = None

        response = html_client_anon_services.post(
            "/user/verify",
            data={"email": "new@example.com", "code": "123456"},
        )

        assert response.status_code == 200
        assert "Код не найден или истёк" in response.text

    def test_verify_wrong_code(self, html_client_anon_services, mock_redis_service):
        mock_redis_service.get_verification_data.return_value = {
            "code": "111111",
            "username": "newuser",
            "email": "new@example.com",
            "hashed_password": "hash",
            "telegram_id": "",
        }

        response = html_client_anon_services.post(
            "/user/verify",
            data={"email": "new@example.com", "code": "000000"},
        )

        assert response.status_code == 200
        assert "Неверный код" in response.text

    def test_verify_create_user_failed(
        self, html_client_anon_services, mock_user_service, mock_redis_service
    ):
        mock_redis_service.get_verification_data.return_value = {
            "code": "123456",
            "username": "newuser",
            "email": "new@example.com",
            "hashed_password": "hash",
            "telegram_id": "",
        }
        mock_user_service.create_user.return_value = None

        response = html_client_anon_services.post(
            "/user/verify",
            data={"email": "new@example.com", "code": "123456"},
        )

        assert response.status_code == 200
        assert "Ошибка регистрации" in response.text

    def test_verify_success(
        self, html_client_anon_services, mock_user_service, mock_redis_service, mock_user
    ):
        mock_redis_service.get_verification_data.return_value = {
            "code": "123456",
            "username": "newuser",
            "email": "new@example.com",
            "hashed_password": "hash",
            "telegram_id": "",
        }
        mock_user_service.create_user.return_value = mock_user

        response = html_client_anon_services.post(
            "/user/verify",
            data={"email": "new@example.com", "code": "123456"},
        )

        assert response.status_code == 200
        assert "Регистрация прошла успешно" in response.text
        mock_user_service.create_user.assert_awaited_once()
