from unittest.mock import patch, MagicMock

from prospect_clients.src.services.automations_service import AutomationsService


class TestAutomationsService:
    @patch("prospect_clients.src.services.automations_service.publish_message")
    def test_activate_maps_scraping(self, mock_publish):
        service = AutomationsService()
        result = service.activate_maps_scraping(
            search_text="pizzarias SP",
            message_user="Ola!",
            user_id=1,
            token="tok123",
            title="Pizzarias",
        )

        assert result == {"message": "Scraping process started"}
        mock_publish.assert_called_once_with(
            "prospect/maps",
            {
                "status": 1,
                "search_text": "pizzarias SP",
                "title": "Pizzarias",
                "user_id": 1,
                "token": "tok123",
                "message_user": "Ola!",
            },
        )

    @patch("prospect_clients.src.services.automations_service.publish_message")
    def test_deactivate_maps_scraping(self, mock_publish):
        service = AutomationsService()
        result = service.deactivate_maps_scraping(
            id_operation=42, user_id=1, token="tok123"
        )

        assert result == {"message": "Scraping process stopped"}
        mock_publish.assert_called_once_with(
            "prospect/maps",
            {
                "status": 0,
                "id_operation": 42,
                "user_id": 1,
                "token": "tok123",
            },
        )

    @patch("prospect_clients.src.services.automations_service.publish_message")
    def test_activate_without_title(self, mock_publish):
        service = AutomationsService()
        result = service.activate_maps_scraping(
            search_text="lojas", message_user="Oi", user_id=2, token="t"
        )

        assert result["message"] == "Scraping process started"
        call_payload = mock_publish.call_args[0][1]
        assert call_payload["title"] is None


class TestAutomationsEndpoints:
    @patch("prospect_clients.src.services.automations_service.publish_message")
    def test_activate_endpoint(self, mock_publish, client):
        # Create user and get token
        client.post("/users/", json={"email": "auto@test.com", "password": "pass"})
        login = client.post(
            "/users/login", data={"username": "auto@test.com", "password": "pass"}
        )
        token = login.json()["access_token"]

        response = client.post(
            "/automations/operations/maps/activate",
            params={"serach_text": "padarias", "message_user": "Ola"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Scraping process started"
        mock_publish.assert_called_once()

    @patch("prospect_clients.src.services.automations_service.publish_message")
    def test_deactivate_endpoint(self, mock_publish, client):
        client.post("/users/", json={"email": "deact@test.com", "password": "pass"})
        login = client.post(
            "/users/login", data={"username": "deact@test.com", "password": "pass"}
        )
        token = login.json()["access_token"]

        response = client.put(
            "/automations/operations/maps/deactivate",
            params={"id_operation": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Scraping process stopped"

    def test_activate_unauthenticated(self, client):
        response = client.post(
            "/automations/operations/maps/activate",
            params={"serach_text": "test", "message_user": "oi"},
        )
        assert response.status_code in (401, 403)
