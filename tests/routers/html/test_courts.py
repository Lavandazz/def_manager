from datetime import date
from types import SimpleNamespace


class TestGetCourts:
    def test_courts_unauthorized(self, html_client_anon_services):
        response = html_client_anon_services.get("/user/courts/")

        assert response.status_code == 200
        assert "войдите или зарегистрируйтесь" in response.text.lower() or (
            "Для отображения календаря" in response.text
        )

    def test_courts_empty(self, html_client_full, mock_court_service):
        mock_court_service.get_courts.return_value = []

        response = html_client_full.get("/user/courts/")

        assert response.status_code == 200
        assert "Календарь судебных заседаний" in response.text
        mock_court_service.get_courts.assert_awaited_once_with(user_id=1)

    def test_courts_with_sessions(self, html_client_full, mock_court_service, html_case):
        court = SimpleNamespace(
            date_court=date(2024, 6, 15),
            time_court="10:00",
            hall_court="Зал 1",
            case=html_case,
        )
        mock_court_service.get_courts.return_value = [court]

        response = html_client_full.get("/user/courts/")

        assert response.status_code == 200
        assert html_case.number_case in response.text
        assert "10:00" in response.text
        assert "Зал 1" in response.text
