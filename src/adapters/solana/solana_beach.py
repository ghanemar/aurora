"""Solana Beach API adapter for Solana blockchain data.

This adapter implements the ChainDataProvider interface for the Solana Beach API,
providing access to validator fees, MEV, rewards, and metadata for Solana validators.

API Documentation: https://api.solanabeach.io/docs
"""

from datetime import UTC, datetime

from adapters.base import (
    ChainDataProvider,
    Period,
    StakeRewards,
    ValidatorFees,
    ValidatorMeta,
    ValidatorMEV,
)
from adapters.exceptions import (
    ProviderDataNotFoundError,
    ProviderError,
    ProviderValidationError,
)
from pydantic import ValidationError


class SolanaBeachAdapter(ChainDataProvider):
    """Adapter for Solana Beach API.

    Provides access to Solana validator data including fees, rewards, and metadata
    through the Solana Beach API endpoints.
    """

    def __init__(
        self,
        provider_name: str = "solana_beach",
        base_url: str = "https://api.solanabeach.io/v1",
        api_key: str | None = None,
        timeout: int = 30,
        rate_limit_per_second: int = 10,
        retry_attempts: int = 3,
    ) -> None:
        """Initialize Solana Beach adapter.

        Args:
            provider_name: Name of the provider (for logging and errors)
            base_url: Base URL for Solana Beach API
            api_key: Optional API key for authentication
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

        Args:
            start: Start of time range (UTC)
            end: End of time range (UTC)

        Returns:
            List of Period objects representing finalized epochs

        Raises:
            ProviderError: If request fails
        """
        try:
            # Fetch epoch information from Solana Beach
            # Note: Solana Beach API endpoint may vary - adjust as needed
            response = await self._request(
                "GET",
                "/epochs",
                params={
                    "start": int(start.timestamp()),
                    "end": int(end.timestamp()),
                },
            )

            periods = []
            for epoch_data in response.get("epochs", []):
                # Only include finalized epochs
                if epoch_data.get("status") == "finalized":
                    period = Period(
                        period_id=str(epoch_data["epoch"]),
                        start_time=datetime.fromtimestamp(
                            epoch_data["start_time"], tz=UTC
                        ),
                        end_time=datetime.fromtimestamp(
                            epoch_data["end_time"], tz=UTC
                        ),
                        metadata={
                            "slot_range": epoch_data.get("slot_range", []),
                            "total_blocks": epoch_data.get("total_blocks", 0),
                        },
                    )
                    periods.append(period)

            return periods

        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                f"Failed to list periods: {str(e)}",
                provider_name=self.provider_name,
            ) from e

    async def get_validator_period_fees(
        self, period: Period, validator_identity: str
    ) -> ValidatorFees:
        """Fetch execution fees for a validator in a specific epoch.

        Args:
            period: Period (epoch) to fetch fees for
            validator_identity: Validator's vote account public key

        Returns:
            ValidatorFees object with fee data

        Raises:
            ProviderDataNotFoundError: If validator or epoch not found
            ProviderError: If request fails
        """
        try:
            # Fetch validator fees for the epoch
            response = await self._request(
                "GET",
                f"/validator/{validator_identity}/fees",
                params={"epoch": period.period_id},
            )

            # Handle case where validator has no data for this epoch
            if not response or response.get("total_fees") is None:
                raise ProviderDataNotFoundError(
                    f"No fee data for validator {validator_identity} in epoch {period.period_id}",
                    provider_name=self.provider_name,
                    resource_type="validator_fees",
                    resource_id=f"{validator_identity}/{period.period_id}",
                )

            try:
                return ValidatorFees(
                    validator_key=validator_identity,
                    total_fees=int(response.get("total_fees", 0)),
                    fee_count=int(response.get("transaction_count", 0)),
                    period_id=period.period_id,
                )
            except (ValidationError, ValueError) as e:
                raise ProviderValidationError(
                    f"Invalid fee data from provider: {str(e)}",
                    provider_name=self.provider_name,
                    details={"response": response},
                ) from e

        except (ProviderDataNotFoundError, ProviderValidationError):
            raise
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                f"Failed to fetch validator fees: {str(e)}",
                provider_name=self.provider_name,
            ) from e

    async def get_validator_period_mev(
        self, period: Period, validator_identity: str
    ) -> ValidatorMEV:
        """Fetch MEV tips for a validator in a specific epoch.

        Note: Solana Beach may not directly provide MEV data. This should
        be fetched from Jito or similar MEV-specific providers.

        Args:
            period: Period (epoch) to fetch MEV for
            validator_identity: Validator's vote account public key

        Returns:
            ValidatorMEV object with MEV data

        Raises:
            ProviderDataNotFoundError: If validator or epoch not found
            ProviderError: If request fails
        """
        try:
            # Note: Solana Beach may not have MEV data
            # This is a placeholder - actual MEV data should come from Jito
            response = await self._request(
                "GET",
                f"/validator/{validator_identity}/mev",
                params={"epoch": period.period_id},
            )

            if not response or response.get("total_mev") is None:
                # Return zero MEV if not available
                return ValidatorMEV(
                    validator_key=validator_identity,
                    total_mev=0,
                    tip_count=0,
                    period_id=period.period_id,
                )

            try:
                return ValidatorMEV(
                    validator_key=validator_identity,
                    total_mev=int(response.get("total_mev", 0)),
                    tip_count=int(response.get("tip_count", 0)),
                    period_id=period.period_id,
                )
            except (ValidationError, ValueError) as e:
                raise ProviderValidationError(
                    f"Invalid MEV data from provider: {str(e)}",
                    provider_name=self.provider_name,
                    details={"response": response},
                ) from e

        except ProviderValidationError:
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

        Args:
            period: Period (epoch) to fetch rewards for
            validator_identity: Validator's vote account public key

        Returns:
            List of StakeRewards objects (one per staker)

        Raises:
            ProviderDataNotFoundError: If validator or epoch not found
            ProviderError: If request fails
        """
        try:
            response = await self._request(
                "GET",
                f"/validator/{validator_identity}/rewards",
                params={"epoch": period.period_id},
            )

            if not response or not response.get("rewards"):
                raise ProviderDataNotFoundError(
                    f"No reward data for validator {validator_identity} in epoch {period.period_id}",
                    provider_name=self.provider_name,
                    resource_type="stake_rewards",
                    resource_id=f"{validator_identity}/{period.period_id}",
                )

            rewards_list = []
            try:
                for reward_data in response.get("rewards", []):
                    rewards = StakeRewards(
                        validator_key=validator_identity,
                        staker_address=reward_data.get("staker_address"),
                        rewards=int(reward_data.get("rewards", 0)),
                        commission=int(reward_data.get("commission", 0)),
                        period_id=period.period_id,
                    )
                    rewards_list.append(rewards)

                return rewards_list

            except (ValidationError, ValueError) as e:
                raise ProviderValidationError(
                    f"Invalid reward data from provider: {str(e)}",
                    provider_name=self.provider_name,
                    details={"response": response},
                ) from e

        except (ProviderDataNotFoundError, ProviderValidationError):
            raise
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                f"Failed to fetch stake rewards: {str(e)}",
                provider_name=self.provider_name,
            ) from e

    async def get_validator_meta(
        self, period: Period, validator_identity: str
    ) -> ValidatorMeta:
        """Fetch validator metadata for a specific epoch.

        Args:
            period: Period (epoch) to fetch metadata for
            validator_identity: Validator's vote account public key

        Returns:
            ValidatorMeta object with validator metadata

        Raises:
            ProviderDataNotFoundError: If validator or epoch not found
            ProviderError: If request fails
        """
        try:
            response = await self._request(
                "GET",
                f"/validator/{validator_identity}",
                params={"epoch": period.period_id},
            )

            if not response:
                raise ProviderDataNotFoundError(
                    f"No metadata for validator {validator_identity} in epoch {period.period_id}",
                    provider_name=self.provider_name,
                    resource_type="validator_meta",
                    resource_id=f"{validator_identity}/{period.period_id}",
                )

            try:
                # Commission rate in Solana is typically 0-100, convert to bps
                commission_pct = float(response.get("commission", 0))
                commission_bps = int(commission_pct * 100)

                return ValidatorMeta(
                    validator_key=validator_identity,
                    commission_rate_bps=commission_bps,
                    is_mev_enabled=bool(response.get("mev_enabled", False)),
                    total_stake=int(response.get("total_stake", 0)),
                    period_id=period.period_id,
                )

            except (ValidationError, ValueError) as e:
                raise ProviderValidationError(
                    f"Invalid metadata from provider: {str(e)}",
                    provider_name=self.provider_name,
                    details={"response": response},
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
