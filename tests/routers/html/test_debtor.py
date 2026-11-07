from shared.config.db.models import DebtorType


class TestChoiceDebtor:
    def test_choice_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.get("/user/debtor/choice_debtor")

        assert response.status_code == 200
        assert "Необходимо авторизоваться" in response.text

    def test_choice_empty(self, html_client_full, mock_case_service):
        mock_case_service.get_user_cases_by_type.return_value = []

        response = html_client_full.get("/user/debtor/choice_debtor")

        assert response.status_code == 200
        assert "Редактирование данных должника" in response.text
        mock_case_service.get_user_cases_by_type.assert_awaited_once_with(
            user_id=1, debtor_type="PHYSICAL"
        )

    def test_choice_with_cases(self, html_client_full, mock_case_service, html_case):
        mock_case_service.get_user_cases_by_type.return_value = [html_case]

        response = html_client_full.get("/user/debtor/choice_debtor")

        assert response.status_code == 200
        assert html_case.debtor.name in response.text
        assert html_case.number_case in response.text


class TestDebtorEditGet:
    def test_edit_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.get("/user/debtor/10/edit")

        assert response.status_code == 200
        assert "Необходимо авторизоваться" in response.text

    def test_edit_not_found(self, html_client_full, mock_debtor_service):
        mock_debtor_service.get_debtor.return_value = None

        response = html_client_full.get("/user/debtor/10/edit")

        assert response.status_code == 404

    def test_edit_form_success(
        self,
        html_client_full,
        mock_debtor_service,
        mock_debtor_detail,
        mock_debtor,
    ):
        mock_debtor_service.get_debtor.return_value = mock_debtor_detail

        response = html_client_full.get(f"/user/debtor/{mock_debtor.id}/edit")

        assert response.status_code == 200
        assert "Редактирование должника" in response.text
        assert mock_debtor.name in response.text
        assert 'name="debtor_type"' in response.text
        # action формы должен указывать на тот же путь (исправленный POST)
        assert f'action="http://testserver/user/debtor/{mock_debtor.id}/edit"' in response.text
        mock_debtor_service.get_debtor.assert_awaited_once_with(1, mock_debtor.id)


class TestDebtorEditPost:
    def _form_data(self, mock_debtor, **overrides):
        data = {
            "debtor_type": DebtorType.PHYSICAL.value,
            "name": mock_debtor.name,
            "inn": str(mock_debtor.inn or ""),
            "snils": str(mock_debtor.snils or ""),
            "birthday": "1990-01-15",
            "birth_region_mode": "existing",
            "birth_region_id": "",
            "new_birth_region_name": "",
            "new_birth_region_city": "",
            "residential_address_mode": "existing",
            "residential_address_id": "",
            "new_ra_region_name": "",
            "new_ra_city": "",
            "new_ra_street": "",
            "new_ra_house": "",
            "new_ra_building": "",
            "new_ra_flat": "",
        }
        data.update(overrides)
        return data

    def test_post_unauthorized(self, html_client_anon_services, mock_debtor):
        response = html_client_anon_services.post(
            f"/user/debtor/{mock_debtor.id}/edit",
            data=self._form_data(mock_debtor),
        )

        assert response.status_code == 200
        assert "Необходимо авторизоваться" in response.text

    def test_post_success(
        self, html_client_full, mock_debtor_service, mock_debtor
    ):
        mock_debtor_service.update_debtor.return_value = mock_debtor

        response = html_client_full.post(
            f"/user/debtor/{mock_debtor.id}/edit",
            data=self._form_data(mock_debtor),
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"].endswith(
            f"/user/debtor/{mock_debtor.id}/edit"
        )
        mock_debtor_service.update_debtor.assert_awaited_once()

    def test_post_validation_error_from_service(
        self,
        html_client_full,
        mock_debtor_service,
        mock_debtor_detail,
        mock_debtor,
    ):
        mock_debtor_service.update_debtor.side_effect = ValueError("Некорректный ИНН")
        mock_debtor_service.get_debtor.return_value = mock_debtor_detail

        response = html_client_full.post(
            f"/user/debtor/{mock_debtor.id}/edit",
            data=self._form_data(mock_debtor),
        )

        assert response.status_code == 200
        assert "Некорректный ИНН" in response.text
        assert "Форма содержит ошибки" in response.text

    def test_post_account_errors(
        self,
        html_client_full,
        mock_debtor_service,
        mock_debtor_detail,
        mock_debtor,
    ):
        mock_debtor_service.get_debtor.return_value = mock_debtor_detail
        data = self._form_data(mock_debtor)
        # номер счёта без банка → ошибка парсера формы
        data["account_number[]"] = "40817810000000000001"
        data["account_bank_id[]"] = ""
        data["account_id[]"] = ""

        response = html_client_full.post(
            f"/user/debtor/{mock_debtor.id}/edit",
            data=data,
        )

        assert response.status_code == 200
        assert "выберите банк" in response.text
        mock_debtor_service.update_debtor.assert_not_awaited()

    def test_old_wrong_path_not_found(self, html_client_full, mock_debtor):
        """Старый путь /debtors/{id}/edit больше не должен существовать."""
        response = html_client_full.post(
            f"/user/debtor/debtors/{mock_debtor.id}/edit",
            data=self._form_data(mock_debtor),
        )

        assert response.status_code == 404
