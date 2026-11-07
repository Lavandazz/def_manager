class TestHelpIndex:
    def test_help_index_anon(self, html_client_anon):
        response = html_client_anon.get("/help/")

        assert response.status_code == 200
        assert "Справочный центр" in response.text
        assert "Инструкция пользователя" in response.text or "Документация" in response.text

    def test_help_index_authenticated(self, html_client):
        response = html_client.get("/help/")

        assert response.status_code == 200
        assert "Справочный центр" in response.text
        assert "testuser" in response.text


class TestHelpAboutPortal:
    def test_about_portal_anon(self, html_client_anon):
        response = html_client_anon.get("/help/about-portal")

        assert response.status_code == 200
        assert "Руководство пользователя" in response.text or "О портале" in response.text

    def test_about_portal_authenticated(self, html_client):
        response = html_client.get("/help/about-portal")

        assert response.status_code == 200
        assert "testuser" in response.text


class TestHelpDebtorEdit:
    def test_debtor_edit_help(self, html_client):
        response = html_client.get("/help/debtor-edit")

        assert response.status_code == 200
        assert "Как редактировать данные должника" in response.text


class TestHelpDebtorFaq:
    def test_debtor_faq(self, html_client):
        response = html_client.get("/help/debtor-faq")

        assert response.status_code == 200
        assert "Частые вопросы по данным должника" in response.text
