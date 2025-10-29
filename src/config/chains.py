"""Chain configuration registry.

This module provides the ChainRegistry class for loading and accessing
blockchain network configurations from YAML files.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from src.config.models import ChainConfig


class ChainConfigError(Exception):
    """Exception raised for chain configuration errors."""

    pass


class ChainRegistry:
    """Registry for blockchain network configurations.

    This class loads chain configurations from a YAML file and provides
    methods to access chain information with validation.

    Attributes:
        chains: Dictionary mapping chain_id to ChainConfig objects
    """

    def __init__(self, config_path: Path | str = Path("config/chains.yaml")) -> None:
        """Initialize the ChainRegistry.

        Args:
            config_path: Path to the chains configuration YAML file

        Raises:
            ChainConfigError: If the configuration file cannot be loaded or is invalid
        """
        self.chains: dict[str, ChainConfig] = {}
        self._config_path = Path(config_path)
        self._load_chains()

    def _load_chains(self) -> None:
        """Load chain configurations from the YAML file.

        Raises:
            ChainConfigError: If the file doesn't exist, can't be parsed, or contains invalid data
        """
        if not self._config_path.exists():
            raise ChainConfigError(f"Chain configuration file not found: {self._config_path}")

        try:
            with open(self._config_path, encoding="utf-8") as f:
                data: dict[str, Any] = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ChainConfigError(f"Invalid YAML in chains configuration: {e}") from e
        except Exception as e:
            raise ChainConfigError(f"Failed to read chains configuration file: {e}") from e

        if not isinstance(data, dict) or "chains" not in data:
            raise ChainConfigError("Invalid chains configuration: must contain 'chains' key")

        chains_data = data["chains"]
        if not isinstance(chains_data, list):
            raise ChainConfigError("Invalid chains configuration: 'chains' must be a list")

        for idx, chain_data in enumerate(chains_data):
            try:
                chain_config = ChainConfig(**chain_data)
                if chain_config.chain_id in self.chains:
                    raise ChainConfigError(
                        f"Duplicate chain_id '{chain_config.chain_id}' in configuration"
                    )
                self.chains[chain_config.chain_id] = chain_config
            except ValidationError as e:
                raise ChainConfigError(f"Invalid chain configuration at index {idx}: {e}") from e

        if not self.chains:
            raise ChainConfigError("No valid chain configurations found")

    def get_chain(self, chain_id: str) -> ChainConfig:
        """Get chain configuration by chain_id.

        Args:
            chain_id: Unique identifier for the chain

        Returns:
            ChainConfig object for the requested chain

        Raises:
            ValueError: If the chain_id is not found in the registry
        """
        if chain_id not in self.chains:
            available_chains = ", ".join(sorted(self.chains.keys()))
            raise ValueError(
                f"Chain '{chain_id}' not found in registry. "
                f"Available chains: {available_chains}"
            )
        return self.chains[chain_id]

    def list_chains(self) -> list[str]:
        """Get a list of all registered chain IDs.

        Returns:
            Sorted list of chain IDs
        """
        return sorted(self.chains.keys())

    def has_chain(self, chain_id: str) -> bool:
        """Check if a chain is registered.

        Args:
            chain_id: Unique identifier for the chain

        Returns:
            True if the chain is registered, False otherwise
        """
        return chain_id in self.chains

    def __len__(self) -> int:
        """Get the number of registered chains."""
        return len(self.chains)

    def __repr__(self) -> str:
        """String representation of the ChainRegistry."""
        return f"ChainRegistry(chains={len(self.chains)}, path={self._config_path})"
