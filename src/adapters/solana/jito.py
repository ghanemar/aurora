"""Jito MEV adapter for fetching MEV tips from Jito API.

This module provides an adapter for the Jito MEV API, specifically for fetching
MEV (Maximal Extractable Value) tip data for validators on Solana. The Jito API
provides historical MEV rewards data per validator per epoch.
"""

from datetime import UTC, datetime

from pydantic import ValidationError

from src.adapters.base import (
    ChainDataProvider,
    Period,
    StakeRewards,
    ValidatorFees,
    ValidatorMEV,
    ValidatorMeta,
)
from src.adapters.exceptions import (
    ProviderDataNotFoundError,
    ProviderError,
    ProviderValidationError,
)


class JitoAdapter(ChainDataProvider):
    """Adapter for Jito MEV API.

    Provides access to MEV tip distribution data for Solana validators through
    the Jito API endpoints. This adapter focuses on MEV-specific data and does
    not provide general validator data (fees, rewards, metadata) - use other
    adapters like SolanaBeachAdapter for that data.

    API Documentation: https://jito-foundation.gitbook.io/mev
    Base URL: https://kobe.mainnet.jito.network
    """

    def __init__(
        self,
        provider_name: str = "jito",
        base_url: str = "https://kobe.mainnet.jito.network",
        api_key: str | None = None,
        timeout: int = 30,
        rate_limit_per_second: int = 10,
        retry_attempts: int = 3,
    ) -> None:
        """Initialize Jito adapter.

        Args:
            provider_name: Name of the provider (for logging and errors)
            base_url: Base URL for Jito API
            api_key: Optional API key for authentication (not currently required)
            timeout: Request timeout in seconds
            rate_limit_per_second: Maximum requests per second
            retry_attempts: Number of retry attempts for failed requests
        """
        super().__init__(
            provider_name=provider_name,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            rate_limit_per_second=rate_limit_per_second,
            retry_attempts=retry_attempts,
        )

    async def list_periods(self, start: datetime, end: datetime) -> list[Period]:
        """List finalized epochs within the given time range.

        Note: Jito API does not provide epoch listing functionality. This method
        is not supported and will raise NotImplementedError. Use another adapter
        (e.g., SolanaBeachAdapter) for epoch discovery.

        Args:
            start: Start of time range (UTC)
            end: End of time range (UTC)

        Returns:
            List of Period objects representing finalized epochs

        Raises:
            NotImplementedError: This method is not supported by Jito API
        """
        raise NotImplementedError(
            "Jito API does not support epoch listing. "
            "Use SolanaBeachAdapter or another provider for epoch discovery."
        )

    async def get_validator_period_fees(
        self, period: Period, validator_identity: str
    ) -> ValidatorFees:
        """Fetch execution fees for a validator in a specific epoch.

        Note: Jito API focuses on MEV data and does not provide fee data. This
        method is not supported. Use another adapter for fee data.

        Args:
            period: Period (epoch) to fetch fees for
            validator_identity: Validator's vote account public key

        Returns:
            ValidatorFees object with fee data

        Raises:
            NotImplementedError: This method is not supported by Jito API
        """
        raise NotImplementedError(
            "Jito API does not provide fee data. "
            "Use SolanaBeachAdapter or another provider for fee information."
        )

    async def get_validator_period_mev(
        self, period: Period, validator_identity: str
    ) -> ValidatorMEV:
        """Fetch MEV tips for a validator in a specific epoch.

        This is the primary method for JitoAdapter, fetching MEV reward data
        from the Jito API for a specific validator and epoch. The API returns
        historical MEV data including pre-commission rewards and commission rates.

        Args:
            period: Period (epoch) to fetch MEV for
            validator_identity: Validator's vote account public key

        Returns:
            ValidatorMEV object with MEV data

        Raises:
            ProviderDataNotFoundError: If validator or epoch not found
            ProviderValidationError: If response data is invalid
            ProviderError: If request fails
        """
        try:
            # Fetch validator MEV history
            # Endpoint: GET /api/v1/validators/{vote_account}
            # Returns array of epoch data sorted by epoch (desc)
            response = await self._request(
                "GET",
                f"/api/v1/validators/{validator_identity}",
            )

            # Response is an array of epoch data, find matching epoch
            if not response or not isinstance(response, list):
                raise ProviderDataNotFoundError(
                    f"No MEV data available for validator {validator_identity}",
                    provider_name=self.provider_name,
                    resource_type="validator_mev",
                    resource_id=validator_identity,
                )

            # Find the specific epoch in the response
            epoch_data = None
            for item in response:
                if str(item.get("epoch")) == period.period_id:
                    epoch_data = item
                    break

            if epoch_data is None:
                # Return zero MEV if epoch not found (validator may not have earned MEV)
                return ValidatorMEV(
                    validator_key=validator_identity,
                    total_mev=0,
                    tip_count=0,
                    period_id=period.period_id,
                )

            try:
                # mev_rewards is in lamports (1 SOL = 1e9 lamports)
                # This is pre-validator commission as noted in docs
                total_mev = int(epoch_data.get("mev_rewards", 0))

                # Note: tip_count is not provided by Jito API, set to 0 if no MEV
                # or 1 if MEV exists (indicating at least one tip distribution)
                tip_count = 1 if total_mev > 0 else 0

                return ValidatorMEV(
                    validator_key=validator_identity,
                    total_mev=total_mev,
                    tip_count=tip_count,
                    period_id=period.period_id,
                )

            except (ValidationError, ValueError) as e:
                raise ProviderValidationError(
                    f"Invalid MEV data from provider: {str(e)}",
                    provider_name=self.provider_name,
                    details={"response": epoch_data},
                ) from e

        except (ProviderDataNotFoundError, ProviderValidationError):
            raise
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                f"Failed to fetch validator MEV: {str(e)}",
                provider_name=self.provider_name,
            ) from e

    async def get_stake_rewards(
        self, period: Period, validator_identity: str
    ) -> list[StakeRewards]:
        """Fetch staking rewards for a validator in a specific epoch.

        Note: Jito API focuses on MEV data and does not provide staking rewards.
        This method is not supported. Use another adapter for rewards data.

        Args:
            period: Period (epoch) to fetch rewards for
            validator_identity: Validator's vote account public key

        Returns:
            List of StakeRewards objects (one per staker)

        Raises:
            NotImplementedError: This method is not supported by Jito API
        """
        raise NotImplementedError(
            "Jito API does not provide staking rewards data. "
            "Use SolanaBeachAdapter or another provider for rewards information."
        )

    async def get_validator_meta(
        self, period: Period, validator_identity: str
    ) -> ValidatorMeta:
        """Fetch validator metadata for a specific epoch.

        Note: Jito API provides limited metadata (only MEV commission). For
        complete validator metadata, use another adapter. This method extracts
        MEV commission rate from the API response.

        Args:
            period: Period (epoch) to fetch metadata for
            validator_identity: Validator's vote account public key

        Returns:
            ValidatorMeta object with limited metadata (MEV commission only)

        Raises:
            ProviderDataNotFoundError: If validator or epoch not found
            ProviderValidationError: If response data is invalid
            ProviderError: If request fails
        """
        try:
            # Fetch validator MEV history for metadata
            response = await self._request(
                "GET",
                f"/api/v1/validators/{validator_identity}",
            )

            if not response or not isinstance(response, list):
                raise ProviderDataNotFoundError(
                    f"No data available for validator {validator_identity}",
                    provider_name=self.provider_name,
                    resource_type="validator_meta",
                    resource_id=validator_identity,
                )

            # Find the specific epoch in the response
            epoch_data = None
            for item in response:
                if str(item.get("epoch")) == period.period_id:
                    epoch_data = item
                    break

            if epoch_data is None:
                raise ProviderDataNotFoundError(
                    f"No metadata for validator {validator_identity} in epoch {period.period_id}",
                    provider_name=self.provider_name,
                    resource_type="validator_meta",
                    resource_id=f"{validator_identity}/{period.period_id}",
                )

            try:
                # Commission rate is provided in basis points (bps)
                commission_bps = int(epoch_data.get("mev_commission_bps", 0))

                # Determine MEV enabled status based on data presence
                is_mev_enabled = bool(epoch_data.get("mev_rewards", 0) > 0)

                # Note: Jito API doesn't provide total_stake, set to 0
                return ValidatorMeta(
                    validator_key=validator_identity,
                    commission_rate_bps=commission_bps,
                    is_mev_enabled=is_mev_enabled,
                    total_stake=0,  # Not provided by Jito API
                    period_id=period.period_id,
                )

            except (ValidationError, ValueError) as e:
                raise ProviderValidationError(
                    f"Invalid metadata from provider: {str(e)}",
                    provider_name=self.provider_name,
                    details={"response": epoch_data},
                ) from e

        except (ProviderDataNotFoundError, ProviderValidationError):
            raise
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                f"Failed to fetch validator metadata: {str(e)}",
                provider_name=self.provider_name,
            ) from e
