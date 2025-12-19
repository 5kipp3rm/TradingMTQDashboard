"""
Configuration Validator

Validates account configurations before worker creation.

Design Pattern: Strategy Pattern for different validation strategies
"""

import logging
from typing import List, Tuple

from src.config.v2.models import AccountConfig
from src.services.worker_manager.models import ValidationResult


logger = logging.getLogger(__name__)


class AccountConfigurationValidator:
    """
    Validates account configurations

    Performs fail-fast validation to catch errors before worker creation.

    Validates:
    - Required fields present
    - MT5 credentials valid format
    - Risk parameters in acceptable ranges
    - Currency configurations valid

    SOLID: Single Responsibility - only validates configurations
    """

    def validate(self, config: AccountConfig) -> ValidationResult:
        """
        Validate account configuration

        Args:
            config: Account configuration to validate

        Returns:
            ValidationResult with validation status
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Validate account ID
        if not config.account_id or not config.account_id.strip():
            errors.append("Account ID is required")

        # Validate default_risk parameters
        if config.default_risk:
            # Validate risk_percent
            if config.default_risk.risk_percent <= 0:
                errors.append(
                    f"risk_percent must be positive, got {config.default_risk.risk_percent}"
                )
            elif config.default_risk.risk_percent > 10:
                warnings.append(
                    f"risk_percent is high ({config.default_risk.risk_percent}%), "
                    "consider reducing"
                )

            # Validate max_positions
            if config.default_risk.max_positions <= 0:
                errors.append(
                    f"max_positions must be positive, got {config.default_risk.max_positions}"
                )

            # Validate portfolio_risk_percent if present
            if config.default_risk.portfolio_risk_percent is not None:
                if config.default_risk.portfolio_risk_percent <= 0:
                    errors.append(
                        f"portfolio_risk_percent must be positive, got {config.default_risk.portfolio_risk_percent}"
                    )
                elif config.default_risk.portfolio_risk_percent > 20:
                    warnings.append(
                        f"portfolio_risk_percent is very high ({config.default_risk.portfolio_risk_percent}%), "
                        "consider reducing"
                    )

            # Validate max_concurrent_trades if present
            if config.default_risk.max_concurrent_trades is not None:
                if config.default_risk.max_concurrent_trades <= 0:
                    errors.append(
                        f"max_concurrent_trades must be positive, got {config.default_risk.max_concurrent_trades}"
                    )
        else:
            warnings.append("No default risk parameters configured, will use system defaults")

        # Validate currency configurations
        if not config.currencies or len(config.currencies) == 0:
            errors.append("No currencies configured for trading")
        else:
            for currency in config.currencies:
                if not currency.symbol or not currency.symbol.strip():
                    errors.append("Currency symbol cannot be empty")

                if currency.enabled and not currency.symbol:
                    errors.append(
                        f"Currency at index {config.currencies.index(currency)} "
                        "is enabled but has no symbol"
                    )

        # Log validation result
        if errors:
            logger.warning(
                f"Configuration validation failed for account {config.account_id}: "
                f"{len(errors)} errors"
            )
        elif warnings:
            logger.info(
                f"Configuration validation passed for account {config.account_id} "
                f"with {len(warnings)} warnings"
            )
        else:
            logger.debug(f"Configuration validation passed for account {config.account_id}")

        return ValidationResult(
            valid=len(errors) == 0,
            account_id=config.account_id,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    def validate_batch(
        self, configs: List[AccountConfig]
    ) -> List[ValidationResult]:
        """
        Validate multiple configurations

        Args:
            configs: List of configurations to validate

        Returns:
            List of validation results
        """
        return [self.validate(config) for config in configs]

    def get_invalid_configs(
        self, configs: List[AccountConfig]
    ) -> List[Tuple[AccountConfig, ValidationResult]]:
        """
        Get list of invalid configurations with their validation results

        Args:
            configs: List of configurations to check

        Returns:
            List of (config, validation_result) tuples for invalid configs
        """
        invalid = []
        for config in configs:
            result = self.validate(config)
            if not result.valid:
                invalid.append((config, result))
        return invalid
