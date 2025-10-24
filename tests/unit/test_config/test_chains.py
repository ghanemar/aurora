"""Unit tests for chain configuration registry."""

import tempfile
from pathlib import Path

import pytest
import yaml

from config.chains import ChainConfigError, ChainRegistry
from config.models import PeriodType


@pytest.fixture
def valid_chains_yaml() -> str:
    """Fixture providing valid chains YAML content."""
    return """
chains:
  - chain_id: "solana-mainnet"
    name: "Solana Mainnet"
    period_type: "EPOCH"
    native_unit: "SOL"
    native_decimals: 9
    finality_lag: 32
    providers:
      fees: "solana_beach"
      mev: "jito"
      rewards: "solana_beach"
      meta: "solana_beach"
      rpc_url: "https://api.mainnet-beta.solana.com"

  - chain_id: "ethereum-mainnet"
    name: "Ethereum Mainnet"
    period_type: "BLOCK_WINDOW"
    native_unit: "ETH"
    native_decimals: 18
    finality_lag: 64
    providers:
      fees: "etherscan"
      mev: "flashbots"
      rewards: "beaconchain"
      meta: "etherscan"
      rpc_url: "https://mainnet.infura.io/v3/test"
"""


@pytest.fixture
def valid_chains_file(valid_chains_yaml: str) -> Path:
    """Fixture providing a temporary valid chains YAML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(valid_chains_yaml)
        return Path(f.name)


class TestChainRegistryInit:
    """Tests for ChainRegistry initialization."""

    def test_load_valid_chains(self, valid_chains_file: Path) -> None:
        """Test loading valid chains configuration."""
        registry = ChainRegistry(config_path=valid_chains_file)
        assert len(registry) == 2
        assert "solana-mainnet" in registry.chains
        assert "ethereum-mainnet" in registry.chains

    def test_file_not_found_raises_error(self) -> None:
        """Test that missing config file raises ChainConfigError."""
        with pytest.raises(ChainConfigError) as exc_info:
            ChainRegistry(config_path="nonexistent.yaml")
        assert "not found" in str(exc_info.value)

    def test_invalid_yaml_raises_error(self) -> None:
        """Test that invalid YAML raises ChainConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content:\n  - unclosed: [bracket")
            invalid_file = Path(f.name)

        with pytest.raises(ChainConfigError) as exc_info:
            ChainRegistry(config_path=invalid_file)
        assert "Invalid YAML" in str(exc_info.value)

    def test_missing_chains_key_raises_error(self) -> None:
        """Test that missing 'chains' key raises ChainConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("wrong_key:\n  - chain_id: test")
            invalid_file = Path(f.name)

        with pytest.raises(ChainConfigError) as exc_info:
            ChainRegistry(config_path=invalid_file)
        assert "must contain 'chains' key" in str(exc_info.value)

    def test_chains_not_a_list_raises_error(self) -> None:
        """Test that non-list chains value raises ChainConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("chains:\n  chain_id: not_a_list")
            invalid_file = Path(f.name)

        with pytest.raises(ChainConfigError) as exc_info:
            ChainRegistry(config_path=invalid_file)
        assert "'chains' must be a list" in str(exc_info.value)

    def test_duplicate_chain_id_raises_error(self) -> None:
        """Test that duplicate chain_id raises ChainConfigError."""
        yaml_content = """
chains:
  - chain_id: "test-chain"
    name: "Test Chain 1"
    period_type: "EPOCH"
    native_unit: "TEST"
    native_decimals: 9
    finality_lag: 10
    providers:
      fees: "test"
      mev: "test"
      rewards: "test"
      meta: "test"
      rpc_url: "https://test.com"

  - chain_id: "test-chain"
    name: "Test Chain 2"
    period_type: "EPOCH"
    native_unit: "TEST"
    native_decimals: 9
    finality_lag: 10
    providers:
      fees: "test"
      mev: "test"
      rewards: "test"
      meta: "test"
      rpc_url: "https://test.com"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            duplicate_file = Path(f.name)

        with pytest.raises(ChainConfigError) as exc_info:
            ChainRegistry(config_path=duplicate_file)
        assert "Duplicate chain_id" in str(exc_info.value)

    def test_invalid_chain_data_raises_error(self) -> None:
        """Test that invalid chain data raises ChainConfigError."""
        yaml_content = """
chains:
  - chain_id: "test-chain"
    # missing required fields
    name: "Test Chain"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            invalid_file = Path(f.name)

        with pytest.raises(ChainConfigError) as exc_info:
            ChainRegistry(config_path=invalid_file)
        assert "Invalid chain configuration" in str(exc_info.value)

    def test_empty_chains_list_raises_error(self) -> None:
        """Test that empty chains list raises ChainConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("chains: []")
            empty_file = Path(f.name)

        with pytest.raises(ChainConfigError) as exc_info:
            ChainRegistry(config_path=empty_file)
        assert "No valid chain configurations found" in str(exc_info.value)


class TestChainRegistryGetChain:
    """Tests for ChainRegistry.get_chain method."""

    def test_get_existing_chain(self, valid_chains_file: Path) -> None:
        """Test getting an existing chain."""
        registry = ChainRegistry(config_path=valid_chains_file)
        chain = registry.get_chain("solana-mainnet")
        assert chain.chain_id == "solana-mainnet"
        assert chain.name == "Solana Mainnet"
        assert chain.period_type == PeriodType.EPOCH
        assert chain.native_unit == "SOL"
        assert chain.native_decimals == 9
        assert chain.finality_lag == 32

    def test_get_nonexistent_chain_raises_error(self, valid_chains_file: Path) -> None:
        """Test that getting nonexistent chain raises ValueError."""
        registry = ChainRegistry(config_path=valid_chains_file)
        with pytest.raises(ValueError) as exc_info:
            registry.get_chain("nonexistent-chain")
        error_message = str(exc_info.value)
        assert "not found in registry" in error_message
        assert "Available chains:" in error_message

    def test_get_chain_returns_correct_provider_map(
        self, valid_chains_file: Path
    ) -> None:
        """Test that get_chain returns correct provider map."""
        registry = ChainRegistry(config_path=valid_chains_file)
        chain = registry.get_chain("solana-mainnet")
        assert chain.providers.fees == "solana_beach"
        assert chain.providers.mev == "jito"
        assert chain.providers.rewards == "solana_beach"
        assert chain.providers.meta == "solana_beach"
        assert chain.providers.rpc_url == "https://api.mainnet-beta.solana.com"


class TestChainRegistryListChains:
    """Tests for ChainRegistry.list_chains method."""

    def test_list_chains_returns_sorted_ids(self, valid_chains_file: Path) -> None:
        """Test that list_chains returns sorted chain IDs."""
        registry = ChainRegistry(config_path=valid_chains_file)
        chain_ids = registry.list_chains()
        assert chain_ids == ["ethereum-mainnet", "solana-mainnet"]
        assert chain_ids == sorted(chain_ids)


class TestChainRegistryHasChain:
    """Tests for ChainRegistry.has_chain method."""

    def test_has_chain_returns_true_for_existing_chain(
        self, valid_chains_file: Path
    ) -> None:
        """Test that has_chain returns True for existing chain."""
        registry = ChainRegistry(config_path=valid_chains_file)
        assert registry.has_chain("solana-mainnet") is True
        assert registry.has_chain("ethereum-mainnet") is True

    def test_has_chain_returns_false_for_nonexistent_chain(
        self, valid_chains_file: Path
    ) -> None:
        """Test that has_chain returns False for nonexistent chain."""
        registry = ChainRegistry(config_path=valid_chains_file)
        assert registry.has_chain("nonexistent-chain") is False


class TestChainRegistryLen:
    """Tests for ChainRegistry.__len__ method."""

    def test_len_returns_chain_count(self, valid_chains_file: Path) -> None:
        """Test that len returns correct chain count."""
        registry = ChainRegistry(config_path=valid_chains_file)
        assert len(registry) == 2


class TestChainRegistryRepr:
    """Tests for ChainRegistry.__repr__ method."""

    def test_repr_contains_chain_count(self, valid_chains_file: Path) -> None:
        """Test that repr contains chain count."""
        registry = ChainRegistry(config_path=valid_chains_file)
        repr_str = repr(registry)
        assert "ChainRegistry" in repr_str
        assert "chains=2" in repr_str
        assert str(valid_chains_file) in repr_str
