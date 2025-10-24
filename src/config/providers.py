"""Provider configuration registry.

This module provides the ProviderRegistry class for loading and accessing
data provider configurations from YAML files.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from config.models import ProviderConfig


class ProviderConfigError(Exception):
    """Exception raised for provider configuration errors."""

    pass


class ProviderRegistry:
    """Registry for data provider configurations.

    This class loads provider configurations from a YAML file and provides
    methods to access provider information with validation. It also supports
    loading API keys from environment variables.

    Attributes:
        providers: Dictionary mapping provider_name to ProviderConfig objects
    """

    def __init__(
        self, config_path: Path | str = Path("config/providers.yaml")
    ) -> None:
        """Initialize the ProviderRegistry.

        Args:
            config_path: Path to the providers configuration YAML file

        Raises:
            ProviderConfigError: If the configuration file cannot be loaded or is invalid
        """
        self.providers: dict[str, ProviderConfig] = {}
        self._config_path = Path(config_path)
        self._load_providers()

    def _load_providers(self) -> None:
        """Load provider configurations from the YAML file.

        Raises:
            ProviderConfigError: If the file doesn't exist, can't be parsed, or contains invalid data
        """
        if not self._config_path.exists():
            raise ProviderConfigError(
                f"Provider configuration file not found: {self._config_path}"
            )

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data: dict[str, Any] = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ProviderConfigError(
                f"Invalid YAML in providers configuration: {e}"
            ) from e
        except Exception as e:
            raise ProviderConfigError(
                f"Failed to read providers configuration file: {e}"
            ) from e

        if not isinstance(data, dict) or "providers" not in data:
            raise ProviderConfigError(
                "Invalid providers configuration: must contain 'providers' key"
            )

        providers_data = data["providers"]
        if not isinstance(providers_data, list):
            raise ProviderConfigError(
                "Invalid providers configuration: 'providers' must be a list"
            )

        for idx, provider_data in enumerate(providers_data):
            try:
                # Check for API key in environment variables
                provider_name = provider_data.get("provider_name")
                if provider_name:
                    env_var_name = f"{provider_name.upper()}_API_KEY"
                    env_api_key = os.environ.get(env_var_name)
                    if env_api_key and not provider_data.get("api_key"):
                        provider_data["api_key"] = env_api_key

                provider_config = ProviderConfig(**provider_data)
                if provider_config.provider_name in self.providers:
                    raise ProviderConfigError(
                        f"Duplicate provider_name '{provider_config.provider_name}' in configuration"
                    )
                self.providers[provider_config.provider_name] = provider_config
            except ValidationError as e:
                raise ProviderConfigError(
                    f"Invalid provider configuration at index {idx}: {e}"
                ) from e

        if not self.providers:
            raise ProviderConfigError("No valid provider configurations found")

    def get_provider(self, provider_name: str) -> ProviderConfig:
        """Get provider configuration by provider_name.

        Args:
            provider_name: Unique identifier for the provider

        Returns:
            ProviderConfig object for the requested provider

        Raises:
            ValueError: If the provider_name is not found in the registry
        """
        if provider_name not in self.providers:
            available_providers = ", ".join(sorted(self.providers.keys()))
            raise ValueError(
                f"Provider '{provider_name}' not found in registry. "
                f"Available providers: {available_providers}"
            )
        return self.providers[provider_name]

    def list_providers(self, enabled_only: bool = False) -> list[str]:
        """Get a list of all registered provider names.

        Args:
            enabled_only: If True, only return enabled providers

        Returns:
            Sorted list of provider names
        """
        if enabled_only:
            return sorted(
                name for name, config in self.providers.items() if config.enabled
            )
        return sorted(self.providers.keys())

    def has_provider(self, provider_name: str) -> bool:
        """Check if a provider is registered.

        Args:
            provider_name: Unique identifier for the provider

        Returns:
            True if the provider is registered, False otherwise
        """
        return provider_name in self.providers

    def is_provider_enabled(self, provider_name: str) -> bool:
        """Check if a provider is enabled.

        Args:
            provider_name: Unique identifier for the provider

        Returns:
            True if the provider is registered and enabled, False otherwise
        """
        if provider_name not in self.providers:
            return False
        return self.providers[provider_name].enabled

    def __len__(self) -> int:
        """Get the number of registered providers."""
        return len(self.providers)

    def __repr__(self) -> str:
        """String representation of the ProviderRegistry."""
        enabled_count = sum(1 for p in self.providers.values() if p.enabled)
        return (
            f"ProviderRegistry(providers={len(self.providers)}, "
            f"enabled={enabled_count}, path={self._config_path})"
        )
