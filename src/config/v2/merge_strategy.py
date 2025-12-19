"""
Configuration V2 Merge Strategies - Strategy Pattern Implementation

Provides different strategies for merging configuration dictionaries.

Design Pattern: Strategy Pattern
- Encapsulates merge algorithms
- Allows runtime selection of merge strategy
- Open/Closed: easy to add new strategies

SOLID: Open/Closed - open for extension, closed for modification
"""

from typing import Dict, Any, List
import logging
from copy import deepcopy

from src.config.v2.interfaces import IMergeStrategy


logger = logging.getLogger(__name__)


class DefaultMergeStrategy(IMergeStrategy):
    """
    Default configuration merge strategy

    Merge behavior:
    - Override values take precedence over base values
    - None values in override are skipped (don't override)
    - Nested dictionaries are merged recursively
    - Lists are replaced (not merged) by default

    Example:
        base = {"a": 1, "b": {"c": 2}}
        override = {"b": {"d": 3}, "e": 4}
        result = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
    """

    def merge(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any],
        merge_lists: bool = False
    ) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries

        Args:
            base: Base configuration (lower priority)
            override: Override configuration (higher priority)
            merge_lists: If True, merge list values; if False, override replaces

        Returns:
            Merged configuration dictionary
        """
        # Start with a deep copy of base to avoid mutations
        result = deepcopy(base)

        for key, override_value in override.items():
            # Skip None values in override (don't override with None)
            if override_value is None:
                continue

            # If key doesn't exist in base, just add it
            if key not in result:
                result[key] = deepcopy(override_value)
                continue

            base_value = result[key]

            # Both values are dicts - merge recursively
            if isinstance(base_value, dict) and isinstance(override_value, dict):
                result[key] = self.merge(base_value, override_value, merge_lists)

            # Both values are lists - merge or replace
            elif isinstance(base_value, list) and isinstance(override_value, list):
                if merge_lists:
                    # Merge lists (extend)
                    result[key] = base_value + [
                        item for item in override_value if item not in base_value
                    ]
                else:
                    # Replace list
                    result[key] = deepcopy(override_value)

            # Otherwise, override value takes precedence
            else:
                result[key] = deepcopy(override_value)

        return result

    def merge_multiple(
        self,
        configs: List[Dict[str, Any]],
        merge_lists: bool = False
    ) -> Dict[str, Any]:
        """
        Merge multiple configurations in order

        Args:
            configs: List of configurations (ascending priority)
            merge_lists: If True, merge list values

        Returns:
            Merged configuration dictionary
        """
        if not configs:
            return {}

        # Start with first config
        result = deepcopy(configs[0])

        # Merge each subsequent config
        for config in configs[1:]:
            result = self.merge(result, config, merge_lists)

        return result


class DeepMergeStrategy(IMergeStrategy):
    """
    Deep merge strategy with advanced list handling

    Merge behavior:
    - Merges nested structures deeply
    - Lists are merged by default (can be disabled)
    - Supports merging lists of dictionaries by ID
    - Handles complex nested structures

    Example (list of dicts merge):
        base = [{"id": 1, "name": "A"}]
        override = [{"id": 1, "value": 10}, {"id": 2, "name": "B"}]
        result = [{"id": 1, "name": "A", "value": 10}, {"id": 2, "name": "B"}]
    """

    def __init__(self, list_merge_key: str = "id"):
        """
        Initialize deep merge strategy

        Args:
            list_merge_key: Key to use for merging lists of dicts
        """
        self.list_merge_key = list_merge_key

    def merge(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any],
        merge_lists: bool = True  # Default to True for deep merge
    ) -> Dict[str, Any]:
        """
        Deep merge two configuration dictionaries

        Args:
            base: Base configuration (lower priority)
            override: Override configuration (higher priority)
            merge_lists: If True, merge list values intelligently

        Returns:
            Merged configuration dictionary
        """
        result = deepcopy(base)

        for key, override_value in override.items():
            # Skip None values
            if override_value is None:
                continue

            # Key doesn't exist in base - add it
            if key not in result:
                result[key] = deepcopy(override_value)
                continue

            base_value = result[key]

            # Both are dicts - recursive merge
            if isinstance(base_value, dict) and isinstance(override_value, dict):
                result[key] = self.merge(base_value, override_value, merge_lists)

            # Both are lists - intelligent merge
            elif isinstance(base_value, list) and isinstance(override_value, list):
                if merge_lists:
                    result[key] = self._merge_lists(base_value, override_value)
                else:
                    result[key] = deepcopy(override_value)

            # Otherwise override takes precedence
            else:
                result[key] = deepcopy(override_value)

        return result

    def _merge_lists(self, base_list: List[Any], override_list: List[Any]) -> List[Any]:
        """
        Intelligently merge two lists

        If lists contain dicts with self.list_merge_key, merge by that key.
        Otherwise, extend the list with unique items.

        Args:
            base_list: Base list
            override_list: Override list

        Returns:
            Merged list
        """
        # Check if lists contain dicts with merge key
        if (base_list and isinstance(base_list[0], dict) and
            self.list_merge_key in base_list[0] and
            override_list and isinstance(override_list[0], dict) and
            self.list_merge_key in override_list[0]):

            # Merge lists of dicts by key
            result_dict = {item[self.list_merge_key]: deepcopy(item) for item in base_list}

            for override_item in override_list:
                key_value = override_item[self.list_merge_key]
                if key_value in result_dict:
                    # Merge the dict
                    result_dict[key_value].update(deepcopy(override_item))
                else:
                    # Add new item
                    result_dict[key_value] = deepcopy(override_item)

            return list(result_dict.values())

        else:
            # Simple extend with unique items
            result = deepcopy(base_list)
            for item in override_list:
                if item not in result:
                    result.append(deepcopy(item))
            return result

    def merge_multiple(
        self,
        configs: List[Dict[str, Any]],
        merge_lists: bool = True
    ) -> Dict[str, Any]:
        """
        Deep merge multiple configurations in order

        Args:
            configs: List of configurations (ascending priority)
            merge_lists: If True, merge list values

        Returns:
            Merged configuration dictionary
        """
        if not configs:
            return {}

        result = deepcopy(configs[0])

        for config in configs[1:]:
            result = self.merge(result, config, merge_lists)

        return result


class SelectiveMergeStrategy(IMergeStrategy):
    """
    Selective merge strategy with custom field-level rules

    Allows specifying which fields to merge and which to override.

    Example:
        strategy = SelectiveMergeStrategy(
            merge_fields={"nested_config"},
            override_fields={"version", "timestamp"}
        )
    """

    def __init__(
        self,
        merge_fields: set[str] = None,
        override_fields: set[str] = None
    ):
        """
        Initialize selective merge strategy

        Args:
            merge_fields: Fields to always merge (recursive)
            override_fields: Fields to always override (no merge)
        """
        self.merge_fields = merge_fields or set()
        self.override_fields = override_fields or set()

    def merge(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any],
        merge_lists: bool = False
    ) -> Dict[str, Any]:
        """
        Selectively merge two configuration dictionaries

        Args:
            base: Base configuration (lower priority)
            override: Override configuration (higher priority)
            merge_lists: If True, merge list values

        Returns:
            Merged configuration dictionary
        """
        result = deepcopy(base)

        for key, override_value in override.items():
            # Skip None values
            if override_value is None:
                continue

            # Override field - always replace
            if key in self.override_fields:
                result[key] = deepcopy(override_value)
                continue

            # Merge field - always merge recursively if possible
            if key in self.merge_fields:
                if key in result and isinstance(result[key], dict) and isinstance(override_value, dict):
                    result[key] = self.merge(result[key], override_value, merge_lists)
                else:
                    result[key] = deepcopy(override_value)
                continue

            # Default behavior
            if key not in result:
                result[key] = deepcopy(override_value)
            elif isinstance(result[key], dict) and isinstance(override_value, dict):
                result[key] = self.merge(result[key], override_value, merge_lists)
            else:
                result[key] = deepcopy(override_value)

        return result

    def merge_multiple(
        self,
        configs: List[Dict[str, Any]],
        merge_lists: bool = False
    ) -> Dict[str, Any]:
        """
        Selectively merge multiple configurations

        Args:
            configs: List of configurations (ascending priority)
            merge_lists: If True, merge list values

        Returns:
            Merged configuration dictionary
        """
        if not configs:
            return {}

        result = deepcopy(configs[0])

        for config in configs[1:]:
            result = self.merge(result, config, merge_lists)

        return result
