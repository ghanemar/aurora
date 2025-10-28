"""Unit tests for provider factory.

Tests factory adapter creation, registration, and configuration integration.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from adapters.base import ChainDataProvider
from adapters.exceptions import ProviderError
from adapters.factory import ProviderFactory
from adapters.solana.jito import JitoAdapter
from adapters.solana.solana_beach import SolanaBeachAdapter

from config.chains import ChainRegistry
from config.providers import ProviderRegistry


@pytest.fixture
def chain_registry() -> ChainRegistry:
    """Create ChainRegistry with test configuration."""
    config_path = Path("config/chains.yaml")
    return ChainRegistry(config_path)


@pytest.fixture
def provider_registry() -> ProviderRegistry:
    """Create ProviderRegistry with test configuration."""
    config_path = Path("config/providers.yaml")
    return ProviderRegistry(config_path)


@pytest.fixture
def factory(
    chain_registry: ChainRegistry,
    provider_registry: ProviderRegistry,
) -> ProviderFactory:
    """Create ProviderFactory with registries."""
    return ProviderFactory(chain_registry, provider_registry)


class TestFactoryInitialization:
    """Tests for factory initialization and registration."""

    def test_factory_initialization(
        self,
        chain_registry: ChainRegistry,
        provider_registry: ProviderRegistry,
    ) -> None:
        """Test factory initializes with registries."""
        factory = ProviderFactory(chain_registry, provider_registry)

        assert factory.chain_registry is chain_registry
        assert factory.provider_registry is provider_registry
        assert isinstance(factory._adapter_classes, dict)

    def test_auto_registration(self, factory: ProviderFactory) -> None:
        """Test adapters are auto-registered during initialization."""
        # SolanaBeachAdapter should be auto-registered
        assert factory.is_adapter_registered("solana_beach")
        assert "solana_beach" in factory.get_registered_adapters()

    def test_manual_registration(self, factory: ProviderFactory) -> None:
        """Test manual adapter registration."""

        class MockAdapter(ChainDataProvider):
            """Mock adapter for testing."""

            async def list_periods(self, start, end):
                return []

            async def get_validator_period_fees(self, period, validator_identity):
                pass

            async def get_validator_period_mev(self, period, validator_identity):
                pass

            async def get_stake_rewards(self, period, validator_identity):
                return []

            async def get_validator_meta(self, period, validator_identity):
                pass

        factory.register_adapter("test_provider", MockAdapter)

        assert factory.is_adapter_registered("test_provider")
        assert MockAdapter in factory._adapter_classes.values()

    def test_get_registered_adapters(self, factory: ProviderFactory) -> None:
        """Test getting list of registered adapters."""
        adapters = factory.get_registered_adapters()

        assert isinstance(adapters, list)
        assert "solana_beach" in adapters


class TestFeesAdapterCreation:
    """Tests for fees adapter creation."""

    def test_create_fees_adapter_solana_mainnet(self, factory: ProviderFactory) -> None:
        """Test creating fees adapter for Solana mainnet."""
        adapter = factory.create_fees_adapter("solana-mainnet")

        assert isinstance(adapter, SolanaBeachAdapter)
        assert adapter.provider_name == "solana_beach"
        assert adapter.base_url == "https://api.solanabeach.io/v1"

    def test_create_fees_adapter_solana_testnet(self, factory: ProviderFactory) -> None:
        """Test creating fees adapter for Solana testnet."""
        adapter = factory.create_fees_adapter("solana-testnet")

        assert isinstance(adapter, SolanaBeachAdapter)
        assert adapter.provider_name == "solana_beach"

    def test_create_fees_adapter_invalid_chain(self, factory: ProviderFactory) -> None:
        """Test creating fees adapter with invalid chain ID."""
        with pytest.raises(ValueError) as exc_info:
            factory.create_fees_adapter("invalid-chain")

        assert "not found in registry" in str(exc_info.value)

    def test_create_fees_adapter_unregistered_provider(
        self,
        chain_registry: ChainRegistry,
        provider_registry: ProviderRegistry,
    ) -> None:
        """Test creating adapter with unregistered provider."""
        # Create factory without auto-registration
        factory = ProviderFactory(chain_registry, provider_registry)
        factory._adapter_classes.clear()  # Clear auto-registered adapters

        with pytest.raises(ProviderError) as exc_info:
            factory.create_fees_adapter("solana-mainnet")

        assert "No adapter registered" in str(exc_info.value)


class TestMEVAdapterCreation:
    """Tests for MEV adapter creation."""

    def test_create_mev_adapter_solana(self, factory: ProviderFactory) -> None:
        """Test creating MEV adapter for Solana."""
        adapter = factory.create_mev_adapter("solana-mainnet")

        assert isinstance(adapter, JitoAdapter)
        assert adapter.provider_name == "jito"
        assert adapter.base_url == "https://kobe.mainnet.jito.network"


class TestRewardsAdapterCreation:
    """Tests for rewards adapter creation."""

    def test_create_rewards_adapter_solana(self, factory: ProviderFactory) -> None:
        """Test creating rewards adapter for Solana."""
        adapter = factory.create_rewards_adapter("solana-mainnet")

        assert isinstance(adapter, SolanaBeachAdapter)
        assert adapter.provider_name == "solana_beach"


class TestMetaAdapterCreation:
    """Tests for metadata adapter creation."""

    def test_create_meta_adapter_solana(self, factory: ProviderFactory) -> None:
        """Test creating metadata adapter for Solana."""
        adapter = factory.create_meta_adapter("solana-mainnet")

        assert isinstance(adapter, SolanaBeachAdapter)
        assert adapter.provider_name == "solana_beach"


class TestProviderConfiguration:
    """Tests for provider configuration integration."""

    def test_adapter_uses_provider_config(self, factory: ProviderFactory) -> None:
        """Test adapter uses provider configuration values."""
        adapter = factory.create_fees_adapter("solana-mainnet")

        # Check configuration from providers.yaml
        assert adapter.timeout == 30
        assert adapter.rate_limit_per_second == 10
        assert adapter.retry_attempts == 3

    def test_adapter_with_api_key_from_config(
        self,
        chain_registry: ChainRegistry,
    ) -> None:
        """Test adapter gets API key from provider config."""
        # Create a provider registry with API key set
        with patch("os.environ.get", return_value="test_api_key"):
            provider_registry = ProviderRegistry(Path("config/providers.yaml"))
            factory = ProviderFactory(chain_registry, provider_registry)

            adapter = factory.create_fees_adapter("solana-mainnet")

            # API key should be loaded from environment
            assert adapter.api_key == "test_api_key"


class TestProviderEnablement:
    """Tests for provider enablement checking."""

    def test_disabled_provider_raises_error(
        self,
        chain_registry: ChainRegistry,
    ) -> None:
        """Test that disabled providers cannot create adapters."""
        # Load provider registry and manually disable a provider
        provider_registry = ProviderRegistry(Path("config/providers.yaml"))
        solana_beach_config = provider_registry.get_provider("solana_beach")
        solana_beach_config.enabled = False

        factory = ProviderFactory(chain_registry, provider_registry)

        with pytest.raises(ProviderError) as exc_info:
            factory.create_fees_adapter("solana-mainnet")

        assert "disabled" in str(exc_info.value).lower()


class TestMultipleAdapterCreation:
    """Tests for creating multiple adapters."""

    def test_create_multiple_adapters_for_same_chain(
        self,
        factory: ProviderFactory,
    ) -> None:
        """Test creating multiple adapter types for same chain."""
        fees_adapter = factory.create_fees_adapter("solana-mainnet")
        rewards_adapter = factory.create_rewards_adapter("solana-mainnet")
        meta_adapter = factory.create_meta_adapter("solana-mainnet")

        # All should be SolanaBeachAdapter but different instances
        assert isinstance(fees_adapter, SolanaBeachAdapter)
        assert isinstance(rewards_adapter, SolanaBeachAdapter)
        assert isinstance(meta_adapter, SolanaBeachAdapter)

        # Should be different instances
        assert fees_adapter is not rewards_adapter
        assert rewards_adapter is not meta_adapter

    def test_create_adapters_for_multiple_chains(
        self,
        factory: ProviderFactory,
    ) -> None:
        """Test creating adapters for different chains."""
        mainnet_adapter = factory.create_fees_adapter("solana-mainnet")
        testnet_adapter = factory.create_fees_adapter("solana-testnet")

        # Both should be SolanaBeachAdapter but different instances
        assert isinstance(mainnet_adapter, SolanaBeachAdapter)
        assert isinstance(testnet_adapter, SolanaBeachAdapter)
        assert mainnet_adapter is not testnet_adapter


class TestFactoryEdgeCases:
    """Tests for factory edge cases and error handling."""

    def test_adapter_registration_overwrites_existing(
        self,
        factory: ProviderFactory,
    ) -> None:
        """Test that re-registering adapter overwrites previous registration."""

        class NewAdapter(ChainDataProvider):
            """New adapter implementation."""

            async def list_periods(self, start, end):
                return []

            async def get_validator_period_fees(self, period, validator_identity):
                pass

            async def get_validator_period_mev(self, period, validator_identity):
                pass

            async def get_stake_rewards(self, period, validator_identity):
                return []

            async def get_validator_meta(self, period, validator_identity):
                pass

        # Register new adapter with same name
        factory.register_adapter("solana_beach", NewAdapter)

        # Factory should use new adapter
        adapter = factory.create_fees_adapter("solana-mainnet")
        assert isinstance(adapter, NewAdapter)
        assert not isinstance(adapter, SolanaBeachAdapter)

    def test_is_adapter_registered_returns_false_for_missing(
        self,
        factory: ProviderFactory,
    ) -> None:
        """Test is_adapter_registered returns False for missing adapters."""
        assert not factory.is_adapter_registered("nonexistent_provider")

    def test_get_registered_adapters_returns_empty_when_none(
        self,
        chain_registry: ChainRegistry,
        provider_registry: ProviderRegistry,
    ) -> None:
        """Test get_registered_adapters when no adapters registered."""
        factory = ProviderFactory(chain_registry, provider_registry)
        factory._adapter_classes.clear()

        adapters = factory.get_registered_adapters()
        assert adapters == []
