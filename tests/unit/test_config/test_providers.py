"""Unit tests for provider configuration registry."""

import tempfile
from pathlib import Path

import pytest

from config.providers import ProviderConfigError, ProviderRegistry


@pytest.fixture
def valid_providers_yaml() -> str:
    """Fixture providing valid providers YAML content."""
    return """
providers:
  - provider_name: "solana_beach"
    enabled: true
    base_url: "https://api.solanabeach.io/v1"
    rate_limit: 10
    timeout: 30
    retry_attempts: 3
    metadata:
      description: "Solana Beach API"

  - provider_name: "jito"
    enabled: true
    base_url: "https://kobe.mainnet.jito.network"
    rate_limit: 5
    timeout: 30
    retry_attempts: 3
    metadata:
      mev_focused: true

  - provider_name: "disabled_provider"
    enabled: false
    base_url: "https://example.com"
"""


@pytest.fixture
def valid_providers_file(valid_providers_yaml: str) -> Path:
    """Fixture providing a temporary valid providers YAML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(valid_providers_yaml)
        return Path(f.name)


class TestProviderRegistryInit:
    """Tests for ProviderRegistry initialization."""

    def test_load_valid_providers(self, valid_providers_file: Path) -> None:
        """Test loading valid providers configuration."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        assert len(registry) == 3
        assert "solana_beach" in registry.providers
        assert "jito" in registry.providers
        assert "disabled_provider" in registry.providers

    def test_file_not_found_raises_error(self) -> None:
        """Test that missing config file raises ProviderConfigError."""
        with pytest.raises(ProviderConfigError) as exc_info:
            ProviderRegistry(config_path="nonexistent.yaml")
        assert "not found" in str(exc_info.value)

    def test_invalid_yaml_raises_error(self) -> None:
        """Test that invalid YAML raises ProviderConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content:\n  - unclosed: [bracket")
            invalid_file = Path(f.name)

        with pytest.raises(ProviderConfigError) as exc_info:
            ProviderRegistry(config_path=invalid_file)
        assert "Invalid YAML" in str(exc_info.value)

    def test_missing_providers_key_raises_error(self) -> None:
        """Test that missing 'providers' key raises ProviderConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("wrong_key:\n  - provider_name: test")
            invalid_file = Path(f.name)

        with pytest.raises(ProviderConfigError) as exc_info:
            ProviderRegistry(config_path=invalid_file)
        assert "must contain 'providers' key" in str(exc_info.value)

    def test_providers_not_a_list_raises_error(self) -> None:
        """Test that non-list providers value raises ProviderConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("providers:\n  provider_name: not_a_list")
            invalid_file = Path(f.name)

        with pytest.raises(ProviderConfigError) as exc_info:
            ProviderRegistry(config_path=invalid_file)
        assert "'providers' must be a list" in str(exc_info.value)

    def test_duplicate_provider_name_raises_error(self) -> None:
        """Test that duplicate provider_name raises ProviderConfigError."""
        yaml_content = """
providers:
  - provider_name: "test_provider"
    enabled: true

  - provider_name: "test_provider"
    enabled: false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            duplicate_file = Path(f.name)

        with pytest.raises(ProviderConfigError) as exc_info:
            ProviderRegistry(config_path=duplicate_file)
        assert "Duplicate provider_name" in str(exc_info.value)

    def test_invalid_provider_data_raises_error(self) -> None:
        """Test that invalid provider data raises ProviderConfigError."""
        yaml_content = """
providers:
  - provider_name: ""
    # empty provider name should fail validation
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            invalid_file = Path(f.name)

        with pytest.raises(ProviderConfigError) as exc_info:
            ProviderRegistry(config_path=invalid_file)
        assert "Invalid provider configuration" in str(exc_info.value)

    def test_empty_providers_list_raises_error(self) -> None:
        """Test that empty providers list raises ProviderConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("providers: []")
            empty_file = Path(f.name)

        with pytest.raises(ProviderConfigError) as exc_info:
            ProviderRegistry(config_path=empty_file)
        assert "No valid provider configurations found" in str(exc_info.value)

    def test_api_key_from_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that API key is loaded from environment variable."""
        yaml_content = """
providers:
  - provider_name: "test_provider"
    enabled: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            test_file = Path(f.name)

        # Set environment variable
        monkeypatch.setenv("TEST_PROVIDER_API_KEY", "env-api-key")

        registry = ProviderRegistry(config_path=test_file)
        provider = registry.get_provider("test_provider")
        assert provider.api_key == "env-api-key"

    def test_yaml_api_key_takes_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that YAML API key takes precedence over environment."""
        yaml_content = """
providers:
  - provider_name: "test_provider"
    enabled: true
    api_key: "yaml-api-key"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            test_file = Path(f.name)

        # Set environment variable
        monkeypatch.setenv("TEST_PROVIDER_API_KEY", "env-api-key")

        registry = ProviderRegistry(config_path=test_file)
        provider = registry.get_provider("test_provider")
        assert provider.api_key == "yaml-api-key"


class TestProviderRegistryGetProvider:
    """Tests for ProviderRegistry.get_provider method."""

    def test_get_existing_provider(self, valid_providers_file: Path) -> None:
        """Test getting an existing provider."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        provider = registry.get_provider("solana_beach")
        assert provider.provider_name == "solana_beach"
        assert provider.enabled is True
        assert provider.base_url == "https://api.solanabeach.io/v1"
        assert provider.rate_limit == 10
        assert provider.timeout == 30
        assert provider.retry_attempts == 3

    def test_get_nonexistent_provider_raises_error(self, valid_providers_file: Path) -> None:
        """Test that getting nonexistent provider raises ValueError."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        with pytest.raises(ValueError) as exc_info:
            registry.get_provider("nonexistent_provider")
        error_message = str(exc_info.value)
        assert "not found in registry" in error_message
        assert "Available providers:" in error_message

    def test_get_disabled_provider(self, valid_providers_file: Path) -> None:
        """Test getting a disabled provider."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        provider = registry.get_provider("disabled_provider")
        assert provider.enabled is False


class TestProviderRegistryListProviders:
    """Tests for ProviderRegistry.list_providers method."""

    def test_list_all_providers(self, valid_providers_file: Path) -> None:
        """Test listing all providers."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        providers = registry.list_providers()
        assert providers == ["disabled_provider", "jito", "solana_beach"]
        assert providers == sorted(providers)

    def test_list_enabled_providers_only(self, valid_providers_file: Path) -> None:
        """Test listing only enabled providers."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        providers = registry.list_providers(enabled_only=True)
        assert providers == ["jito", "solana_beach"]
        assert "disabled_provider" not in providers


class TestProviderRegistryHasProvider:
    """Tests for ProviderRegistry.has_provider method."""

    def test_has_provider_returns_true_for_existing_provider(
        self, valid_providers_file: Path
    ) -> None:
        """Test that has_provider returns True for existing provider."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        assert registry.has_provider("solana_beach") is True
        assert registry.has_provider("jito") is True
        assert registry.has_provider("disabled_provider") is True

    def test_has_provider_returns_false_for_nonexistent_provider(
        self, valid_providers_file: Path
    ) -> None:
        """Test that has_provider returns False for nonexistent provider."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        assert registry.has_provider("nonexistent_provider") is False


class TestProviderRegistryIsProviderEnabled:
    """Tests for ProviderRegistry.is_provider_enabled method."""

    def test_is_provider_enabled_returns_true_for_enabled(self, valid_providers_file: Path) -> None:
        """Test that is_provider_enabled returns True for enabled provider."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        assert registry.is_provider_enabled("solana_beach") is True
        assert registry.is_provider_enabled("jito") is True

    def test_is_provider_enabled_returns_false_for_disabled(
        self, valid_providers_file: Path
    ) -> None:
        """Test that is_provider_enabled returns False for disabled provider."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        assert registry.is_provider_enabled("disabled_provider") is False

    def test_is_provider_enabled_returns_false_for_nonexistent(
        self, valid_providers_file: Path
    ) -> None:
        """Test that is_provider_enabled returns False for nonexistent provider."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        assert registry.is_provider_enabled("nonexistent_provider") is False


class TestProviderRegistryLen:
    """Tests for ProviderRegistry.__len__ method."""

    def test_len_returns_provider_count(self, valid_providers_file: Path) -> None:
        """Test that len returns correct provider count."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        assert len(registry) == 3


class TestProviderRegistryRepr:
    """Tests for ProviderRegistry.__repr__ method."""

    def test_repr_contains_provider_count(self, valid_providers_file: Path) -> None:
        """Test that repr contains provider count and enabled count."""
        registry = ProviderRegistry(config_path=valid_providers_file)
        repr_str = repr(registry)
        assert "ProviderRegistry" in repr_str
        assert "providers=3" in repr_str
        assert "enabled=2" in repr_str
        assert str(valid_providers_file) in repr_str
