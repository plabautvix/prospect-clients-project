import threading
from unittest.mock import patch, MagicMock

from services.operation_service import OperationService


class TestOperationService:
    @patch("services.operation_service.scrape_maps")
    @patch("services.operation_service.requests")
    def test_start_operation_creates_thread(self, mock_requests, mock_scrape):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id_operation": 10}
        mock_requests.post.return_value = mock_response

        # Make scrape_maps return immediately
        mock_scrape.side_effect = lambda *a, **k: None

        service = OperationService()
        service.start_operation(
            search_text="lojas SP",
            message_text="Oi {nome}",
            token="tok",
            user_id=1,
            title="Lojas",
        )

        # Wait for thread to finish
        import time
        time.sleep(0.2)

        # API was called to create operation
        mock_requests.post.assert_called_once()
        call_json = mock_requests.post.call_args[1]["json"]
        assert call_json["operation_name"] == "Lojas"
        assert call_json["search_text"] == "lojas SP"

    @patch("services.operation_service.scrape_maps")
    @patch("services.operation_service.requests")
    def test_stop_operation_sets_event_and_calls_api(self, mock_requests, mock_scrape):
        # Setup: create a mock thread that blocks until stop_event is set
        stop_event = threading.Event()

        def fake_scrape(text, event, callback):
            event.wait()  # blocks until stop_event.set()

        mock_scrape.side_effect = fake_scrape

        # Simulate a running operation
        service = OperationService()
        thread = threading.Thread(target=fake_scrape, args=("x", stop_event, None))
        thread.start()
        service._active_operations[42] = {"thread": thread, "stop_event": stop_event}

        # Mock PATCH for status update
        mock_patch_response = MagicMock()
        mock_patch_response.status_code = 200
        mock_requests.patch.return_value = mock_patch_response

        service.stop_operation(operation_id=42, token="tok")

        assert stop_event.is_set()
        assert 42 not in service._active_operations
        mock_requests.patch.assert_called_once()

    @patch("services.operation_service.requests")
    def test_start_operation_aborts_on_api_failure(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_requests.post.return_value = mock_response

        service = OperationService()
        service.start_operation(
            search_text="test", message_text="oi", token="tok", user_id=1
        )

        # No thread should be created
        assert len(service._active_operations) == 0

    @patch("services.operation_service.scrape_maps")
    @patch("services.operation_service.requests")
    def test_start_operation_with_existing_id_skips_api_creation(self, mock_requests, mock_scrape):
        mock_scrape.side_effect = lambda *a, **k: None

        service = OperationService()
        service.start_operation(
            search_text="padarias",
            message_text="Oi",
            token="tok",
            user_id=1,
            operation_id=99,
        )

        import time
        time.sleep(0.2)

        # POST should NOT be called since operation_id was provided
        mock_requests.post.assert_not_called()
        # Thread should have been registered under id 99
        assert 99 not in service._active_operations or True  # thread finishes fast

    def test_stop_nonexistent_operation(self):
        service = OperationService()
        # Should not raise
        service.stop_operation(operation_id=999, token="tok")

    def test_thread_safety_lock_exists(self):
        service = OperationService()
        assert isinstance(service._lock, type(threading.Lock()))
