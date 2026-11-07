from unittest.mock import patch

from shared.utils.exceptions import AccessForbidden


class TestAddCaseForm:
    def test_create_form_unauthorized(self, html_client_anon):
        response = html_client_anon.get("/user/cases/create")

        assert response.status_code == 200
        assert "Главная страница" in response.text or "Арбитражные дела" in response.text

    def test_create_form_success(self, html_client):
        response = html_client.get("/user/cases/create")

        assert response.status_code == 200
        assert "Добавление нового дела" in response.text
        assert 'name="number_case"' in response.text


class TestAddCase:
    def test_add_case_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.post(
            "/user/cases",
            data={
                "number_case": "A40-12345/2024",
                "debtor_type": "physical",
                "debtor_name": "Иванов Иван Иванович",
            },
        )

        # В контексте передаётся error (не message), в layout оно не выводится
        assert response.status_code == 401

    def test_add_case_invalid_number(
        self, html_client_full, mock_debtor_service, mock_case_service
    ):
        response = html_client_full.post(
            "/user/cases",
            data={
                "number_case": "invalid",
                "debtor_type": "physical",
                "debtor_name": "Иванов Иван Иванович",
            },
        )

        assert response.status_code == 400
        assert "Некорректный формат номера дела" in response.text
        mock_debtor_service.add_debtor.assert_not_awaited()
        mock_case_service.add_case.assert_not_awaited()

    def test_add_case_success(
        self, html_client_full, mock_debtor_service, mock_case_service, mock_debtor, html_case
    ):
        mock_debtor_service.add_debtor.return_value = mock_debtor
        mock_case_service.add_case.return_value = html_case

        with patch("web_app.routers.html.case.parsing_task") as mock_task:
            mock_task.delay.return_value = "task-id"
            response = html_client_full.post(
                "/user/cases",
                data={
                    "number_case": "A40-12345/2024",
                    "debtor_type": "physical",
                    "debtor_name": "Иванов Иван Иванович",
                },
            )

        assert response.status_code == 201
        assert "Дело успешно добавлено" in response.text
        mock_debtor_service.add_debtor.assert_awaited_once()
        mock_case_service.add_case.assert_awaited_once()
        mock_task.delay.assert_called_once_with(case_number="A40-12345/2024")


class TestCaseDetail:
    def test_case_detail_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.get("/user/cases/1")

        assert response.status_code == 200
        assert "Необходимо авторизоваться" in response.text

    def test_case_detail_success(
        self, html_client_full, mock_case_service, html_case
    ):
        mock_case_service.get_case.return_value = html_case
        mock_case_service.get_case_documents_paginated.return_value = ([], 0)

        response = html_client_full.get("/user/cases/1")

        assert response.status_code == 200
        assert html_case.number_case in response.text
        assert html_case.debtor.name in response.text
        mock_case_service.get_case.assert_awaited_once_with(case_id=1)
        mock_case_service.get_case_documents_paginated.assert_awaited_once_with(1, 1, 10)


class TestDeleteCase:
    def test_delete_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.post("/user/cases/1/delete")

        assert response.status_code == 401
        assert "Необходимо авторизоваться" in response.text

    def test_delete_success(self, html_client_full, mock_case_service):
        mock_case_service.delete_case.return_value = True

        response = html_client_full.post("/user/cases/1/delete")

        assert response.status_code == 200
        assert "Дело удалено" in response.text
        mock_case_service.delete_case.assert_awaited_once_with(user_id=1, case_id=1)

    def test_delete_not_found(self, html_client_full, mock_case_service):
        mock_case_service.delete_case.return_value = False

        response = html_client_full.post("/user/cases/1/delete")

        assert response.status_code == 409
        assert "уже удалено или не найдено" in response.text

    def test_delete_forbidden(self, html_client_full, mock_case_service):
        mock_case_service.delete_case.side_effect = AccessForbidden()

        response = html_client_full.post("/user/cases/1/delete")

        assert response.status_code == 403
        assert "Ошибка доступа" in response.text


class TestGenerateDocumentsGet:
    def test_generate_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.get("/user/cases/generate_documents/1")

        assert response.status_code == 200
        assert "войдите или зарегистрируйтесь" in response.text.lower() or (
            "Для отображения календаря" in response.text
        )

    def test_generate_case_not_found(self, html_client_full, mock_case_service):
        mock_case_service.get_case_for_documents.return_value = None

        response = html_client_full.get("/user/cases/generate_documents/1")

        assert response.status_code == 404
        assert "Дело не найдено" in response.text

    def test_generate_wrong_owner(self, html_client_full, mock_case_service, html_case):
        html_case.id_user = 999
        mock_case_service.get_case_for_documents.return_value = html_case

        response = html_client_full.get("/user/cases/generate_documents/1")

        assert response.status_code == 404
        assert "Дело не найдено" in response.text

    def test_generate_form_success(self, html_client_full, mock_case_service, html_case):
        mock_case_service.get_case_for_documents.return_value = html_case

        response = html_client_full.get("/user/cases/generate_documents/1")

        assert response.status_code == 200
        assert "Данные для генерации документа" in response.text
        assert html_case.number_case in response.text


class TestGenerateDocumentsPost:
    def test_generate_post_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.post(
            "/user/cases/generate_documents/1",
            data={"region_court": "Московской области"},
        )

        assert response.status_code == 401
        assert "Необходимо авторизоваться" in response.text

    def test_generate_post_not_found(self, html_client_full, mock_case_service):
        mock_case_service.get_case_for_documents.return_value = None

        response = html_client_full.post(
            "/user/cases/generate_documents/1",
            data={"region_court": "Московской области"},
        )

        assert response.status_code == 404
        assert "Дело не найдено" in response.text

    def test_generate_post_success(
        self, html_client_full, mock_case_service, mock_document_service, html_case
    ):
        html_case.debtor.accounts = []
        mock_case_service.get_case_for_documents.return_value = html_case
        mock_document_service.generate_request_doc.return_value = []
        mock_document_service.generate_banks_docs.return_value = []

        response = html_client_full.post(
            "/user/cases/generate_documents/1",
            data={"region_court": "Московской области"},
        )

        assert response.status_code == 200
        assert html_case.number_case in response.text
        mock_document_service.generate_request_doc.assert_awaited_once()
        mock_document_service.generate_banks_docs.assert_awaited_once()


class TestDownloadDocument:
    def test_download_unauthorized(self, html_client_anon):
        response = html_client_anon.get("/user/cases/download/subdir/file.docx")

        assert response.status_code == 401
        assert "Необходимо авторизоваться" in response.text

    def test_download_path_traversal(self, html_client):
        response = html_client.get("/user/cases/download/../etc/passwd")

        # либо 400 от нашей проверки, либо 404 от роутинга
        assert response.status_code in (400, 404)

    def test_download_bad_filename(self, html_client):
        response = html_client.get("/user/cases/download/sub..dir/file.docx")

        assert response.status_code == 400
        assert "Некорректный путь" in response.text

    def test_download_not_found(self, html_client, tmp_path, monkeypatch):
        monkeypatch.setattr("web_app.routers.html.case.OUTPUT_DIR", tmp_path)

        response = html_client.get("/user/cases/download/subdir/missing.docx")

        assert response.status_code == 404
        assert "Файл не найден" in response.text

    def test_download_success(self, html_client, tmp_path, monkeypatch):
        monkeypatch.setattr("web_app.routers.html.case.OUTPUT_DIR", tmp_path)
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file_path = subdir / "doc.docx"
        file_path.write_bytes(b"PK fake docx")

        response = html_client.get("/user/cases/download/subdir/doc.docx")

        assert response.status_code == 200
        assert response.content == b"PK fake docx"
