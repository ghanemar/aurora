"""Factory for creating chain-specific data provider adapters.

This module provides the ProviderFactory class which instantiates the appropriate
adapter implementation based on chain configuration and provider registry settings.
"""


from adapters.base import ChainDataProvider
from adapters.exceptions import ProviderError

from config.chains import ChainRegistry
from config.models import ProviderConfig
from config.providers import ProviderRegistry


class ProviderFactory:
    """Factory for creating provider adapters based on chain configuration.

    This class uses the ChainRegistry and ProviderRegistry to determine which
    adapter implementation to instantiate for a given chain and data type.
    """

    def __init__(
        self,
        chain_registry: ChainRegistry,
        provider_registry: ProviderRegistry,
    ) -> None:
        """Initialize the ProviderFactory.

        Args:
            chain_registry: Registry containing chain configurations
            provider_registry: Registry containing provider configurations
        """
        self.chain_registry = chain_registry
        self.provider_registry = provider_registry

        # Mapping of provider names to adapter classes
        # This will be populated as adapters are implemented
        self._adapter_classes: dict[str, type[ChainDataProvider]] = {}

        # Auto-register available adapters
        self._register_available_adapters()

    def _register_available_adapters(self) -> None:
        """Automatically register all available adapter implementations."""
        try:
            from adapters.solana.solana_beach import SolanaBeachAdapter

            self.register_adapter("solana_beach", SolanaBeachAdapter)
        except ImportError:
            pass  # Adapter not available

    def register_adapter(
        self,
        provider_name: str,
        adapter_class: type[ChainDataProvider],
    ) -> None:
        """Register an adapter class for a provider.

        Args:
            provider_name: Name of the provider (must match provider registry)
            adapter_class: Adapter class that extends ChainDataProvider
        """
        self._adapter_classes[provider_name] = adapter_class

    def _create_adapter(
        self,
        provider_name: str,
        provider_config: ProviderConfig,
    ) -> ChainDataProvider:
        """Create adapter instance for a provider.

        Args:
            provider_name: Name of the provider
            provider_config: Provider configuration

        Returns:
            Instantiated adapter

        Raises:
            ProviderError: If adapter not registered or provider disabled
        """
        # Check if provider is enabled
        if not provider_config.enabled:
            raise ProviderError(
                f"Provider '{provider_name}' is disabled",
                provider_name=provider_name,
            )

        # Check if adapter class is registered
        if provider_name not in self._adapter_classes:
            raise ProviderError(
                f"No adapter registered for provider '{provider_name}'. "
                f"Available adapters: {', '.join(self._adapter_classes.keys())}",
                provider_name=provider_name,
            )

        adapter_class = self._adapter_classes[provider_name]

        # Create adapter instance with provider configuration
        return adapter_class(
            provider_name=provider_name,
            base_url=provider_config.base_url or "",
            api_key=provider_config.api_key,
            timeout=provider_config.timeout,
            rate_limit_per_second=provider_config.rate_limit,
            retry_attempts=provider_config.retry_attempts,
        )

    def create_fees_adapter(self, chain_id: str) -> ChainDataProvider:
        """Create fees adapter for a specific chain.

        Args:
            chain_id: Chain identifier (e.g., "solana-mainnet")

        Returns:
            Configured fees adapter for the chain

        Raises:
            ValueError: If chain not found
            ProviderError: If provider not available or disabled
        """
        chain_config = self.chain_registry.get_chain(chain_id)
        provider_name = chain_config.providers.fees
        provider_config = self.provider_registry.get_provider(provider_name)

        return self._create_adapter(provider_name, provider_config)

    def create_mev_adapter(self, chain_id: str) -> ChainDataProvider:
        """Create MEV adapter for a specific chain.

        Args:
            chain_id: Chain identifier (e.g., "solana-mainnet")

        Returns:
            Configured MEV adapter for the chain

        Raises:
            ValueError: If chain not found
            ProviderError: If provider not available or disabled
        """
        chain_config = self.chain_registry.get_chain(chain_id)
        provider_name = chain_config.providers.mev
        provider_config = self.provider_registry.get_provider(provider_name)

        return self._create_adapter(provider_name, provider_config)

    def create_rewards_adapter(self, chain_id: str) -> ChainDataProvider:
        """Create rewards adapter for a specific chain.

        Args:
            chain_id: Chain identifier (e.g., "solana-mainnet")

        Returns:
            Configured rewards adapter for the chain

        Raises:
            ValueError: If chain not found
            ProviderError: If provider not available or disabled
        """
        chain_config = self.chain_registry.get_chain(chain_id)
        provider_name = chain_config.providers.rewards
        provider_config = self.provider_registry.get_provider(provider_name)

        return self._create_adapter(provider_name, provider_config)

    def create_meta_adapter(self, chain_id: str) -> ChainDataProvider:
        """Create metadata adapter for a specific chain.

        Args:
            chain_id: Chain identifier (e.g., "solana-mainnet")

        Returns:
            Configured metadata adapter for the chain

        Raises:
            ValueError: If chain not found
            ProviderError: If provider not available or disabled
        """
        chain_config = self.chain_registry.get_chain(chain_id)
        provider_name = chain_config.providers.meta
        provider_config = self.provider_registry.get_provider(provider_name)

        return self._create_adapter(provider_name, provider_config)

    def get_registered_adapters(self) -> list[str]:
        """Get list of registered adapter names.

        Returns:
            List of provider names with registered adapters
        """
        return list(self._adapter_classes.keys())

    def is_adapter_registered(self, provider_name: str) -> bool:
        """Check if adapter is registered for a provider.

        Args:
            provider_name: Name of the provider to check

        Returns:
            True if adapter is registered, False otherwise
        """
        return provider_name in self._adapter_classes
