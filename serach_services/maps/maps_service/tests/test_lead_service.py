from unittest.mock import patch, MagicMock

from services.lead_service import LeadService


class TestLeadService:
    @patch("services.lead_service.requests")
    def test_process_found_leads_sends_to_api(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_requests.post.return_value = mock_response

        service = LeadService(user_id=5, operation_id=9)
        leads = [{"nome": "Lead A", "telefone": "+55111"}]

        service.process_found_leads(leads)

        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert call_args[1]["json"] == leads
        # Authenticates with the service key, not a user token; user_id is passed along.
        assert "X-Service-Key" in call_args[1]["headers"]
        # operation_id ties each lead back to the run that found it.
        assert call_args[1]["params"] == {"user_id": 5, "operation_id": 9}

    @patch("services.lead_service.requests")
    def test_operation_id_is_optional(self, mock_requests):
        mock_requests.post.return_value = MagicMock(status_code=201)

        LeadService(user_id=5).process_found_leads([{"nome": "Lead A"}])

        params = mock_requests.post.call_args[1]["params"]
        assert params == {"user_id": 5, "operation_id": None}

    @patch("services.lead_service.requests")
    def test_api_failure_does_not_crash(self, mock_requests):
        from requests.exceptions import ConnectionError
        mock_requests.post.side_effect = ConnectionError("Connection refused")
        mock_requests.RequestException = Exception

        service = LeadService(user_id=1)
        leads = [{"nome": "Test", "telefone": "+55333"}]

        # Should not raise
        service.process_found_leads(leads)
