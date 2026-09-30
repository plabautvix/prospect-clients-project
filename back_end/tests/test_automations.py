from unittest.mock import patch

from prospect_clients.src.services.automations_service import AutomationsService


class TestAutomationsService:
    @patch("prospect_clients.src.services.automations_service.publish_message")
    def test_activate_maps_scraping(self, mock_publish):
        service = AutomationsService()
        result = service.activate_maps_scraping(
            search_text="pizzarias SP",
            message_user="Ola!",
            user_id=1,
            id_operation=7,
            title="Pizzarias",
        )

        assert result == {"message": "Scraping process started"}
        payload = mock_publish.call_args[0][1]
        assert payload["status"] == 1
        assert payload["id_operation"] == 7
        assert payload["search_text"] == "pizzarias SP"
        # The user token must NOT be propagated to the maps-service.
        assert "token" not in payload

    @patch("prospect_clients.src.services.automations_service.publish_message")
    def test_deactivate_maps_scraping(self, mock_publish):
        service = AutomationsService()
        result = service.deactivate_maps_scraping(id_operation=42, user_id=1)

        assert result == {"message": "Scraping process stopped"}
        mock_publish.assert_called_once_with(
            "prospect/maps",
            {"status": 0, "id_operation": 42, "user_id": 1},
        )

    @patch("prospect_clients.src.services.automations_service.publish_message")
    def test_activate_without_title(self, mock_publish):
        service = AutomationsService()
        service.activate_maps_scraping(
            search_text="lojas", message_user="Oi", user_id=2, id_operation=1
        )
        assert mock_publish.call_args[0][1]["title"] is None

    @patch("prospect_clients.src.services.automations_service.publish_message")
    def test_activate_instagram_search(self, mock_publish):
        service = AutomationsService()
        result = service.activate_instagram_search(
            search_text="medica veterinaria em Campinas",
            user_id=1,
            id_operation=7,
        )

        assert result == {"message": "Instagram search started"}
        mock_publish.assert_called_once_with(
            "prospect/instagram",
            {
                "status": 1,
                "id_operation": 7,
                "search_text": "medica veterinaria em Campinas",
                "user_id": 1,
                "limit": None,
            },
        )
        # The user token must NOT be propagated to the instagram-service.
        assert "token" not in mock_publish.call_args[0][1]

    @patch("prospect_clients.src.services.automations_service.publish_message")
    def test_deactivate_instagram_search(self, mock_publish):
        service = AutomationsService()
        result = service.deactivate_instagram_search(id_operation=42, user_id=1)

        assert result == {"message": "Instagram search stopped"}
        mock_publish.assert_called_once_with(
            "prospect/instagram",
            {"status": 0, "id_operation": 42, "user_id": 1},
        )

    @patch("prospect_clients.src.services.automations_service.publish_message")
    def test_the_lead_limit_reaches_the_service(self, mock_publish):
        AutomationsService().activate_instagram_search(
            search_text="psicologa", user_id=1, id_operation=7, limit=250
        )

        assert mock_publish.call_args[0][1]["limit"] == 250


class TestAutomationsEndpoints:
    @patch("prospect_clients.src.controllers.automations_controller.AutomationsService")
    def test_activate_endpoint_creates_operation(self, mock_service_cls, client):
        mock_service_cls.return_value.activate_maps_scraping.return_value = {"message": "ok"}

        client.post("/users/", json={"email": "auto@test.com", "password": "pass"})
        login = client.post("/users/login", data={"username": "auto@test.com", "password": "pass"})
        token = login.json()["access_token"]

        response = client.post(
            "/automations/operations/maps/activate",
            params={"serach_text": "padarias", "message_user": "Ola"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        # Deve retornar a operação criada no DB
        assert data["operation_name"] == "padarias"
        assert data["search_text"] == "padarias"
        assert data["status"] == 1
        assert "id_operation" in data
        # Maps service deve ter sido chamado com o id_operation
        mock_service_cls.return_value.activate_maps_scraping.assert_called_once()
        call_kwargs = mock_service_cls.return_value.activate_maps_scraping.call_args[1]
        assert call_kwargs["id_operation"] == data["id_operation"]

    @patch("prospect_clients.src.controllers.automations_controller.AutomationsService")
    def test_deactivate_endpoint(self, mock_service_cls, client):
        mock_service_cls.return_value.deactivate_maps_scraping.return_value = {"message": "ok"}

        client.post("/users/", json={"email": "deact@test.com", "password": "pass"})
        login = client.post("/users/login", data={"username": "deact@test.com", "password": "pass"})
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

    @patch("prospect_clients.src.controllers.automations_controller.AutomationsService")
    def test_instagram_activate_endpoint_creates_operation(self, mock_service_cls, client):
        token = self._login(client, "ig@test.com")

        response = client.post(
            "/automations/operations/instagram/activate",
            params={"search_text": "medica veterinaria em Campinas"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["search_text"] == "medica veterinaria em Campinas"
        assert data["status"] == 1
        # The source is what lets the frontend route the deactivate call.
        assert data["source"] == "instagram"

        call_kwargs = mock_service_cls.return_value.activate_instagram_search.call_args[1]
        assert call_kwargs["id_operation"] == data["id_operation"]

    @patch("prospect_clients.src.controllers.automations_controller.AutomationsService")
    def test_maps_operations_still_default_to_the_maps_source(self, mock_service_cls, client):
        token = self._login(client, "src@test.com")

        response = client.post(
            "/automations/operations/maps/activate",
            params={"serach_text": "padarias", "message_user": "Ola"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.json()["source"] == "maps"

    @patch("prospect_clients.src.controllers.automations_controller.AutomationsService")
    def test_instagram_deactivate_endpoint(self, mock_service_cls, client):
        token = self._login(client, "igoff@test.com")

        response = client.put(
            "/automations/operations/instagram/deactivate",
            params={"id_operation": 1},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Instagram search stopped"

    @staticmethod
    def _login(client, email: str) -> str:
        client.post("/users/", json={"email": email, "password": "pass"})
        login = client.post(
            "/users/login", data={"username": email, "password": "pass"}
        )
        return login.json()["access_token"]
