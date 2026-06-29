from unittest.mock import patch, MagicMock

from services.lead_service import LeadService


class TestLeadService:
    @patch("services.lead_service.RabbitMQPublisher")
    @patch("services.lead_service.requests")
    def test_process_found_leads_sends_to_api(self, mock_requests, mock_rmq_cls):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_requests.post.return_value = mock_response

        service = LeadService(user_id=5, message_template="Oi {nome}")
        leads = [{"nome": "Lead A", "telefone": "+55111"}]

        service.process_found_leads(leads)

        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert call_args[1]["json"] == leads
        # Authenticates with the service key, not a user token; user_id is passed along.
        assert "X-Service-Key" in call_args[1]["headers"]
        assert call_args[1]["params"] == {"user_id": 5}

    @patch("services.lead_service.RabbitMQPublisher")
    @patch("services.lead_service.requests")
    def test_process_found_leads_publishes_to_rabbitmq(self, mock_requests, mock_rmq_cls):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_requests.post.return_value = mock_response

        mock_publisher = MagicMock()
        mock_rmq_cls.return_value = mock_publisher

        service = LeadService(user_id=1, message_template="Ola {nome}")
        leads = [{"nome": "Lead B", "telefone": "+55222"}]

        service.process_found_leads(leads)

        mock_publisher.publish.assert_called_once()
        payload = mock_publisher.publish.call_args[0][0]
        assert payload["messages"][0]["lead"] == "+55222"
        assert "Ola Lead B" in payload["messages"][0]["message"]

    @patch("services.lead_service.RabbitMQPublisher")
    @patch("services.lead_service.requests")
    def test_process_leads_without_phone_skips_rabbitmq(self, mock_requests, mock_rmq_cls):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_requests.post.return_value = mock_response

        mock_publisher = MagicMock()
        mock_rmq_cls.return_value = mock_publisher

        service = LeadService(user_id=1, message_template="Oi {nome}")
        leads = [{"nome": "No Phone", "telefone": None}]

        service.process_found_leads(leads)

        # API should still be called
        mock_requests.post.assert_called_once()
        # RabbitMQ should NOT be called (no valid messages)
        mock_publisher.publish.assert_not_called()

    @patch("services.lead_service.RabbitMQPublisher")
    @patch("services.lead_service.requests")
    def test_api_failure_does_not_crash(self, mock_requests, mock_rmq_cls):
        from requests.exceptions import ConnectionError
        mock_requests.post.side_effect = ConnectionError("Connection refused")
        mock_requests.RequestException = Exception

        service = LeadService(user_id=1, message_template="Oi {nome}")
        leads = [{"nome": "Test", "telefone": "+55333"}]

        # Should not raise
        service.process_found_leads(leads)
