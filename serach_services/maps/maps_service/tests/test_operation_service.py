import threading
from unittest.mock import patch, MagicMock

from services.operation_service import OperationService


class TestOperationService:
    @patch("services.operation_service.scrape_maps")
    @patch("services.operation_service.requests")
    def test_start_operation_creates_thread(self, mock_requests, mock_scrape):
        mock_patch_response = MagicMock()
        mock_patch_response.status_code = 200
        mock_requests.patch.return_value = mock_patch_response

        # Make scrape_maps return immediately
        mock_scrape.side_effect = lambda *a, **k: None

        service = OperationService()
        service.start_operation(
            search_text="lojas SP",
            user_id=1,
            operation_id=10,
            title="Lojas",
        )

        # Wait for thread to finish
        import time
        time.sleep(0.2)

        # The maps-service never creates operations via API anymore.
        mock_requests.post.assert_not_called()
        # On finishing it marks the operation stopped via the service endpoint.
        mock_requests.patch.assert_called_once()

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

        service.stop_operation(operation_id=42)

        assert stop_event.is_set()
        assert 42 not in service._active_operations
        mock_requests.patch.assert_called_once()

    @patch("services.operation_service.scrape_maps")
    @patch("services.operation_service.requests")
    def test_start_operation_without_id_aborts(self, mock_requests, mock_scrape):
        service = OperationService()
        service.start_operation(
            search_text="test", user_id=1, operation_id=None
        )

        # No thread should be created and no API call made
        assert len(service._active_operations) == 0
        mock_scrape.assert_not_called()
        mock_requests.patch.assert_not_called()

    @patch("services.operation_service.requests")
    def test_stop_nonexistent_operation(self, mock_requests):
        # Even without a thread in memory (e.g. maps_service was restarted),
        # the database must be reconciled to status=0.
        mock_patch_response = MagicMock()
        mock_patch_response.status_code = 200
        mock_requests.patch.return_value = mock_patch_response

        service = OperationService()
        # Should not raise
        service.stop_operation(operation_id=999)

        mock_requests.patch.assert_called_once()

    def test_thread_safety_lock_exists(self):
        service = OperationService()
        assert isinstance(service._lock, type(threading.Lock()))
