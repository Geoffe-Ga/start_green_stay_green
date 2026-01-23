"""Secure credential management using OS keyring.

This module provides functions for securely storing and retrieving
API keys using the operating system's native keyring service.

The keyring package is optional - if not available or if the keyring
backend is not configured, functions return None gracefully rather
than raising exceptions.

Example:
    >>> from start_green_stay_green.utils.credentials import (
    ...     get_api_key_from_keyring,
    ...     store_api_key_in_keyring,
    ... )
    >>> # Store API key (one-time setup)
    >>> success = store_api_key_in_keyring("sk-ant-api-key-123")
    >>> # Retrieve API key
    >>> api_key = get_api_key_from_keyring()
    >>> if api_key:
    ...     print("API key found in keyring")
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_api_key_from_keyring(
    service: str = "sgsg",
    username: str = "claude_api_key",
) -> str | None:
    """Retrieve Claude API key from OS keyring.

    Attempts to retrieve the API key from the operating system's
    secure keyring service. Returns None gracefully if:
    - keyring package is not installed
    - keyring backend is not available/configured
    - no API key is stored
    - any other error occurs

    Args:
        service: Service identifier for keyring storage.
            Defaults to "sgsg".
        username: Username/key identifier within the service.
            Defaults to "claude_api_key".

    Returns:
        API key string if found, None otherwise.

    Example:
        >>> api_key = get_api_key_from_keyring()
        >>> if api_key:
        ...     print(f"Found API key: {api_key[:10]}...")
        ... else:
        ...     print("No API key in keyring")
    """
    try:
        import keyring  # type: ignore[import-not-found]  # noqa: PLC0415  # Optional dependency

        api_key: str | None = keyring.get_password(service, username)
        if api_key:
            logger.debug("API key retrieved from keyring")
            return api_key
        logger.debug("No API key found in keyring")
        return None  # noqa: TRY300  # Happy path return is clearer
    except ImportError:
        logger.warning("keyring package not available, skipping keyring check")
        return None
    except Exception as e:  # noqa: BLE001  # Graceful degradation for any keyring error
        logger.warning("Failed to retrieve from keyring: %s", e)
        return None


def store_api_key_in_keyring(  # pragma: allowlist secret
    api_key: str,
    service: str = "sgsg",
    username: str = "claude_api_key",
) -> bool:
    """Store Claude API key in OS keyring.

    Attempts to securely store the API key in the operating system's
    keyring service. Returns False if storage fails for any reason:
    - keyring package is not installed
    - keyring backend is not available/configured
    - permission errors
    - any other error

    Args:
        api_key: The Claude API key to store securely.
        service: Service identifier for keyring storage.
            Defaults to "sgsg".
        username: Username/key identifier within the service.
            Defaults to "claude_api_key".

    Returns:
        True if stored successfully, False otherwise.

    Example:
        >>> api_key = "sk-ant-api-key-123456"  # pragma: allowlist secret
        >>> if store_api_key_in_keyring(api_key):
        ...     print("API key stored successfully")
        ... else:
        ...     print("Failed to store API key")
    """
    try:
        import keyring  # noqa: PLC0415  # Optional dependency

        keyring.set_password(service, username, api_key)
        logger.info("API key stored in keyring successfully")
        return True  # noqa: TRY300  # Happy path return is clearer
    except ImportError:
        logger.exception("keyring package not available")
        return False
    except Exception:  # Graceful degradation for any keyring error
        logger.exception("Failed to store in keyring")
        return False
