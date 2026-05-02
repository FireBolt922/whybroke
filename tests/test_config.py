import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import pytest

from whybroke.config import (
    CONFIG_DIR,
    CREDENTIALS_PATH,
    SUPPORTED_PROVIDERS,
    ConfigError,
    delete_credentials,
    load_credentials,
    save_credentials,
)


@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    """Mock the config directory and credentials path."""
    cred_path = tmp_path / "credentials.json"
    monkeypatch.setattr("whybroke.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("whybroke.config.CREDENTIALS_PATH", cred_path)
    return tmp_path, cred_path


class TestLoadCredentials:
    def test_loads_credentials_from_file(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        cred_path.write_text(
            json.dumps({"provider": "openai", "api_key": "test-key"})
        )

        result = load_credentials()
        assert result["provider"] == "openai"
        assert result["api_key"] == "test-key"

    def test_raises_error_when_credentials_not_found(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        with pytest.raises(ConfigError) as exc_info:
            load_credentials()
        assert "No credentials found" in str(exc_info.value)

    def test_handles_json_with_multiple_fields(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        cred_path.write_text(
            json.dumps({
                "provider": "anthropic",
                "api_key": "sk-123",
                "org_id": "org-456",
            })
        )

        result = load_credentials()
        assert result["provider"] == "anthropic"
        assert result["api_key"] == "sk-123"
        assert result["org_id"] == "org-456"

    def test_gracefully_handles_corrupted_json(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        cred_path.write_text("not valid json {")

        with pytest.raises(Exception):
            load_credentials()


class TestSaveCredentials:
    def test_saves_credentials_to_file(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        save_credentials("openai", "test-key-123")

        assert cred_path.exists()
        data = json.loads(cred_path.read_text())
        assert data["provider"] == "openai"
        assert data["api_key"] == "test-key-123"

    def test_creates_config_directory_if_not_exists(self, mock_config_dir, monkeypatch):
        tmp_path, cred_path = mock_config_dir
        nested_dir = tmp_path / "nested" / "config"
        monkeypatch.setattr("whybroke.config.CONFIG_DIR", nested_dir)
        monkeypatch.setattr("whybroke.config.CREDENTIALS_PATH", nested_dir / "creds.json")

        save_credentials("anthropic", "test-key")

        assert (nested_dir / "creds.json").exists()

    def test_rejects_unsupported_provider(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        with pytest.raises(ConfigError) as exc_info:
            save_credentials("invalid_provider", "test-key")
        assert "Unsupported provider" in str(exc_info.value)

    def test_saves_with_all_supported_providers(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        for provider in SUPPORTED_PROVIDERS:
            cred_path.unlink(missing_ok=True)
            save_credentials(provider, f"key-for-{provider}")
            assert cred_path.exists()
            data = json.loads(cred_path.read_text())
            assert data["provider"] == provider

    def test_overwrites_existing_credentials(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        save_credentials("openai", "key1")
        save_credentials("anthropic", "key2")

        data = json.loads(cred_path.read_text())
        assert data["provider"] == "anthropic"
        assert data["api_key"] == "key2"

    def test_sets_secure_file_permissions(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        save_credentials("openai", "test-key")

        # Check that file is readable and writable by owner only
        mode = os.stat(cred_path).st_mode
        # Owner read/write permissions (0o600 = 384)
        assert mode & 0o600 == 0o600
        # No group or other permissions
        assert mode & 0o077 == 0

    def test_handles_permission_error_gracefully(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        # Save credentials first
        save_credentials("openai", "test-key")

        # Mock os.chmod to raise an error
        original_chmod = os.chmod

        def mock_chmod(path, mode):
            raise OSError("Permission denied")

        with mock.patch("os.chmod", side_effect=mock_chmod):
            # Should not raise, just pass silently
            save_credentials("anthropic", "test-key-2")

        assert cred_path.exists()
        data = json.loads(cred_path.read_text())
        assert data["api_key"] == "test-key-2"

    def test_formats_json_with_indentation(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        save_credentials("openai", "test-key")

        content = cred_path.read_text()
        # Should be indented (contains newlines)
        assert "\n" in content
        assert '  ' in content  # indentation


class TestDeleteCredentials:
    def test_deletes_credentials_file(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        cred_path.write_text(json.dumps({"provider": "openai", "api_key": "key"}))
        assert cred_path.exists()

        result = delete_credentials()

        assert not cred_path.exists()
        assert result is True

    def test_returns_false_when_credentials_not_found(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        assert not cred_path.exists()

        result = delete_credentials()

        assert result is False

    def test_returns_true_after_successful_delete(self, mock_config_dir):
        tmp_path, cred_path = mock_config_dir
        cred_path.write_text(json.dumps({"provider": "anthropic", "api_key": "key"}))

        result = delete_credentials()

        assert result is True
        assert not cred_path.exists()


class TestSupportedProviders:
    def test_contains_major_providers(self):
        assert "openai" in SUPPORTED_PROVIDERS
        assert "anthropic" in SUPPORTED_PROVIDERS
        assert "gemini" in SUPPORTED_PROVIDERS

    def test_all_providers_are_lowercase(self):
        for provider in SUPPORTED_PROVIDERS:
            assert provider == provider.lower()

    def test_is_tuple_not_list(self):
        assert isinstance(SUPPORTED_PROVIDERS, tuple)


class TestConfigError:
    def test_is_exception(self):
        assert issubclass(ConfigError, Exception)

    def test_can_be_raised_with_message(self):
        with pytest.raises(ConfigError) as exc_info:
            raise ConfigError("Test error message")
        assert "Test error message" in str(exc_info.value)
