"""
Connector Factory - Create MT4/MT5 instances
Manages multiple connector instances
"""
from typing import Dict, Optional
import logging
from .base import BaseMetaTraderConnector, PlatformType
from .mt5_connector import MT5Connector
from .mt4_connector import MT4Connector


logger = logging.getLogger(__name__)


class ConnectorFactory:
    """
    Factory for creating and managing MetaTrader connector instances
    Supports multiple simultaneous connections
    """
    
    _instances: Dict[str, BaseMetaTraderConnector] = {}
    
    @classmethod
    def create_connector(cls, platform: PlatformType, 
                        instance_id: str = "default") -> BaseMetaTraderConnector:
        """
        Create a new connector instance
        
        Args:
            platform: Platform type (MT4 or MT5)
            instance_id: Unique identifier for this instance
            
        Returns:
            Connector instance
            
        Raises:
            ValueError: If instance_id already exists
        """
        if instance_id in cls._instances:
            logger.warning(f"Instance '{instance_id}' already exists, returning existing")
            return cls._instances[instance_id]
        
        if platform == PlatformType.MT5:
            connector = MT5Connector(instance_id)
        elif platform == PlatformType.MT4:
            connector = MT4Connector(instance_id)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        cls._instances[instance_id] = connector
        logger.info(f"Created connector: {platform.value} - {instance_id}")
        return connector
    
    @classmethod
    def get_connector(cls, instance_id: str) -> Optional[BaseMetaTraderConnector]:
        """
        Get existing connector instance
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            Connector instance or None if not found
        """
        return cls._instances.get(instance_id)
    
    @classmethod
    def remove_connector(cls, instance_id: str) -> bool:
        """
        Remove and disconnect connector instance
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            True if removed successfully
        """
        connector = cls._instances.get(instance_id)
        if connector:
            connector.disconnect()
            del cls._instances[instance_id]
            logger.info(f"Removed connector: {instance_id}")
            return True
        return False
    
    @classmethod
    def get_all_instances(cls) -> Dict[str, BaseMetaTraderConnector]:
        """Get all active connector instances"""
        return cls._instances.copy()
    
    @classmethod
    def disconnect_all(cls) -> None:
        """Disconnect and remove all connector instances"""
        for instance_id in list(cls._instances.keys()):
            cls.remove_connector(instance_id)
        logger.info("All connectors disconnected")
    
    @classmethod
    def get_instance_count(cls) -> int:
        """Get number of active instances"""
        return len(cls._instances)


# Convenience functions for single-instance usage

def create_mt5_connector(instance_id: str = "default") -> MT5Connector:
    """Create MT5 connector (convenience function)"""
    return ConnectorFactory.create_connector(PlatformType.MT5, instance_id)


def create_mt4_connector(instance_id: str = "default") -> MT4Connector:
    """Create MT4 connector (convenience function)"""
    return ConnectorFactory.create_connector(PlatformType.MT4, instance_id)


def get_connector(instance_id: str = "default") -> Optional[BaseMetaTraderConnector]:
    """Get connector by instance ID (convenience function)"""
    return ConnectorFactory.get_connector(instance_id)
