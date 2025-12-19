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

        # Validate MT5 credentials
        if not hasattr(config, 'login') or config.login is None:
            errors.append("MT5 login is required")
        elif config.login <= 0:
            errors.append(f"MT5 login must be positive, got {config.login}")

        if not hasattr(config, 'password') or not config.password:
            errors.append("MT5 password is required")
        elif len(config.password) < 4:
            warnings.append("MT5 password seems too short (< 4 characters)")

        if not hasattr(config, 'server') or not config.server:
            errors.append("MT5 server is required")
        elif not config.server.strip():
            errors.append("MT5 server cannot be empty")

        # Validate risk parameters
        if config.risk:
            if config.risk.max_daily_loss_pct <= 0:
                errors.append(
                    f"max_daily_loss_pct must be positive, got {config.risk.max_daily_loss_pct}"
                )
            elif config.risk.max_daily_loss_pct > 50:
                warnings.append(
                    f"max_daily_loss_pct is very high ({config.risk.max_daily_loss_pct}%), "
                    "consider reducing"
                )

            if config.risk.max_position_size_pct <= 0:
                errors.append(
                    f"max_position_size_pct must be positive, got {config.risk.max_position_size_pct}"
                )
            elif config.risk.max_position_size_pct > 100:
                errors.append(
                    f"max_position_size_pct cannot exceed 100%, got {config.risk.max_position_size_pct}"
                )

            if config.risk.risk_per_trade_pct <= 0:
                errors.append(
                    f"risk_per_trade_pct must be positive, got {config.risk.risk_per_trade_pct}"
                )
            elif config.risk.risk_per_trade_pct > 10:
                warnings.append(
                    f"risk_per_trade_pct is high ({config.risk.risk_per_trade_pct}%), "
                    "consider reducing"
                )
        else:
            warnings.append("No risk parameters configured, will use defaults")

        # Validate currency configurations
        if not config.currencies or len(config.currencies) == 0:
            warnings.append("No currencies configured for trading")
        else:
            for currency in config.currencies:
                if not currency.symbol or not currency.symbol.strip():
                    errors.append("Currency symbol cannot be empty")

                if currency.enabled and not currency.symbol:
                    errors.append(
                        f"Currency at index {config.currencies.index(currency)} "
                        "is enabled but has no symbol"
                    )

        # Validate MT5 connection parameters
        if hasattr(config, 'timeout'):
            if config.timeout <= 0:
                errors.append(f"Connection timeout must be positive, got {config.timeout}")
            elif config.timeout > 300000:  # 5 minutes
                warnings.append(
                    f"Connection timeout is very high ({config.timeout}ms), "
                    "consider reducing"
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
