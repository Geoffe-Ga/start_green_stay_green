"""Unit tests for secure credential management.

Tests the credentials module's ability to store and retrieve API keys
from the OS keyring with proper error handling and graceful degradation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from start_green_stay_green.utils.credentials import get_api_key_from_keyring
from start_green_stay_green.utils.credentials import store_api_key_in_keyring

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestGetApiKeyFromKeyring:
    """Test get_api_key_from_keyring() function."""

    def test_get_api_key_success(self, mocker: MockerFixture) -> None:
        """Test successful API key retrieval from keyring."""
        # Mock keyring module
        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = "sk-ant-test-key-12345"
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Get API key
        api_key = get_api_key_from_keyring()

        # Verify
        assert api_key == "sk-ant-test-key-12345"  # pragma: allowlist secret
        mock_keyring.get_password.assert_called_once_with("sgsg", "claude_api_key")

    def test_get_api_key_with_custom_service_and_username(
        self, mocker: MockerFixture
    ) -> None:
        """Test API key retrieval with custom service and username."""
        # Mock keyring module
        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = "sk-ant-custom-key"
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Get API key with custom parameters
        api_key = get_api_key_from_keyring(
            service="custom-service",
            username="custom-user",
        )

        # Verify
        assert api_key == "sk-ant-custom-key"  # pragma: allowlist secret
        mock_keyring.get_password.assert_called_once_with(
            "custom-service", "custom-user"
        )

    def test_get_api_key_not_found(self, mocker: MockerFixture) -> None:
        """Test graceful handling when API key not found in keyring."""
        # Mock keyring module returning None
        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = None
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Get API key
        api_key = get_api_key_from_keyring()

        # Verify returns None gracefully
        assert api_key is None
        mock_keyring.get_password.assert_called_once()

    def test_get_api_key_keyring_not_installed(self, mocker: MockerFixture) -> None:
        """Test graceful handling when keyring package not installed."""
        # Mock the keyring module to not exist (remove from sys.modules)
        mocker.patch.dict("sys.modules", {"keyring": None})

        # Get API key
        api_key = get_api_key_from_keyring()

        # Verify returns None gracefully
        assert api_key is None

    def test_get_api_key_keyring_backend_error(self, mocker: MockerFixture) -> None:
        """Test graceful handling when keyring backend fails."""
        # Mock keyring module that raises exception
        mock_keyring = MagicMock()
        mock_keyring.get_password.side_effect = RuntimeError(
            "Keyring backend not available"
        )
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Get API key
        api_key = get_api_key_from_keyring()

        # Verify returns None gracefully
        assert api_key is None

    def test_get_api_key_permission_error(self, mocker: MockerFixture) -> None:
        """Test graceful handling of permission errors."""
        # Mock keyring module that raises PermissionError
        mock_keyring = MagicMock()
        mock_keyring.get_password.side_effect = PermissionError("Access denied")
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Get API key
        api_key = get_api_key_from_keyring()

        # Verify returns None gracefully
        assert api_key is None


class TestStoreApiKeyInKeyring:
    """Test store_api_key_in_keyring() function."""

    def test_store_api_key_success(self, mocker: MockerFixture) -> None:
        """Test successful API key storage in keyring."""
        # Mock keyring module
        mock_keyring = MagicMock()
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Store API key
        api_key = "sk-ant-test-key-67890"  # pragma: allowlist secret
        success = store_api_key_in_keyring(api_key)

        # Verify
        assert success
        mock_keyring.set_password.assert_called_once_with(
            "sgsg", "claude_api_key", api_key
        )

    def test_store_api_key_with_custom_service_and_username(
        self, mocker: MockerFixture
    ) -> None:
        """Test API key storage with custom service and username."""
        # Mock keyring module
        mock_keyring = MagicMock()
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Store API key with custom parameters
        api_key = "sk-ant-custom-key-99999"  # pragma: allowlist secret
        success = store_api_key_in_keyring(
            api_key,
            service="my-service",
            username="my-user",
        )

        # Verify
        assert success
        mock_keyring.set_password.assert_called_once_with(
            "my-service", "my-user", api_key
        )

    def test_store_api_key_keyring_not_installed(self, mocker: MockerFixture) -> None:
        """Test graceful handling when keyring package not installed."""
        # Mock the keyring module to not exist (remove from sys.modules)
        mocker.patch.dict("sys.modules", {"keyring": None})

        # Store API key
        success = store_api_key_in_keyring("sk-ant-test-key")

        # Verify returns False gracefully
        assert not success

    def test_store_api_key_keyring_backend_error(self, mocker: MockerFixture) -> None:
        """Test graceful handling when keyring backend fails."""
        # Mock keyring module that raises exception
        mock_keyring = MagicMock()
        mock_keyring.set_password.side_effect = RuntimeError(
            "Keyring backend not available"
        )
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Store API key
        success = store_api_key_in_keyring("sk-ant-test-key")

        # Verify returns False gracefully
        assert not success

    def test_store_api_key_permission_error(self, mocker: MockerFixture) -> None:
        """Test graceful handling of permission errors."""
        # Mock keyring module that raises PermissionError
        mock_keyring = MagicMock()
        mock_keyring.set_password.side_effect = PermissionError("Access denied")
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Store API key
        success = store_api_key_in_keyring("sk-ant-test-key")

        # Verify returns False gracefully
        assert not success

    def test_store_empty_api_key(self, mocker: MockerFixture) -> None:
        """Test storing empty API key (should still succeed at storage level)."""
        # Mock keyring module
        mock_keyring = MagicMock()
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Store empty API key (validation happens at CLI level, not here)
        success = store_api_key_in_keyring("")

        # Verify storage succeeds (validation is caller's responsibility)
        assert success
        mock_keyring.set_password.assert_called_once_with("sgsg", "claude_api_key", "")


class TestCredentialsIntegration:
    """Integration tests for store and retrieve workflow."""

    def test_store_and_retrieve_workflow(self, mocker: MockerFixture) -> None:
        """Test complete workflow of storing then retrieving API key."""
        # Mock keyring module with in-memory storage
        stored_keys: dict[tuple[str, str], str] = {}

        def mock_set_password(service: str, username: str, password: str) -> None:
            stored_keys[(service, username)] = password

        def mock_get_password(service: str, username: str) -> str | None:
            return stored_keys.get((service, username))

        mock_keyring = MagicMock()
        mock_keyring.set_password.side_effect = mock_set_password
        mock_keyring.get_password.side_effect = mock_get_password
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Store API key
        original_key = "sk-ant-integration-test-key"
        store_success = store_api_key_in_keyring(original_key)
        assert store_success

        # Retrieve API key
        retrieved_key = get_api_key_from_keyring()
        assert retrieved_key == original_key

    def test_retrieve_before_store_returns_none(self, mocker: MockerFixture) -> None:
        """Test retrieving before storing returns None."""
        # Mock keyring module with empty storage
        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = None
        mocker.patch.dict("sys.modules", {"keyring": mock_keyring})

        # Try to retrieve without storing first
        api_key = get_api_key_from_keyring()

        # Verify returns None
        assert api_key is None
