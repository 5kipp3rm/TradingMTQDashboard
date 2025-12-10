"""
Unit tests for ConnectorFactory
"""
import pytest

from src.connectors.factory import (
    ConnectorFactory, 
    create_mt5_connector, 
    create_mt4_connector,
    get_connector
)
from src.connectors.base import PlatformType
from src.connectors.mt5_connector import MT5Connector
from src.connectors.mt4_connector import MT4Connector


@pytest.fixture(autouse=True)
def reset_factory():
    """Reset factory state before each test"""
    ConnectorFactory._instances = {}
    yield
    ConnectorFactory.disconnect_all()


class TestConnectorFactory:
    """Test ConnectorFactory class"""
    
    def test_create_mt5_connector(self):
        """Test creating MT5 connector"""
        connector = ConnectorFactory.create_connector(PlatformType.MT5, "test1")
        
        assert connector is not None
        assert isinstance(connector, MT5Connector)
        assert ConnectorFactory.get_instance_count() == 1
    
    def test_create_mt4_connector(self):
        """Test creating MT4 connector"""
        connector = ConnectorFactory.create_connector(PlatformType.MT4, "test1")
        
        assert connector is not None
        assert isinstance(connector, MT4Connector)
        assert ConnectorFactory.get_instance_count() == 1
    
    def test_create_connector_with_default_id(self):
        """Test creating connector with default instance ID"""
        connector = ConnectorFactory.create_connector(PlatformType.MT5)
        
        assert connector is not None
        assert "default" in ConnectorFactory._instances
    
    def test_create_duplicate_instance_returns_existing(self):
        """Test creating duplicate instance returns existing"""
        connector1 = ConnectorFactory.create_connector(PlatformType.MT5, "test1")
        connector2 = ConnectorFactory.create_connector(PlatformType.MT5, "test1")
        
        assert connector1 is connector2
        assert ConnectorFactory.get_instance_count() == 1
    
    def test_create_unsupported_platform(self):
        """Test creating connector with unsupported platform"""
        with pytest.raises(ValueError, match="Unsupported platform"):
            ConnectorFactory.create_connector("INVALID", "test1")
    
    def test_get_connector_existing(self):
        """Test getting existing connector"""
        created = ConnectorFactory.create_connector(PlatformType.MT5, "test1")
        connector = ConnectorFactory.get_connector("test1")
        
        assert connector is created
    
    def test_get_connector_nonexistent(self):
        """Test getting non-existent connector"""
        connector = ConnectorFactory.get_connector("nonexistent")
        assert connector is None
    
    def test_remove_connector(self):
        """Test removing connector"""
        ConnectorFactory.create_connector(PlatformType.MT5, "test1")
        result = ConnectorFactory.remove_connector("test1")
        
        assert result == True
        assert ConnectorFactory.get_instance_count() == 0
    
    def test_remove_nonexistent_connector(self):
        """Test removing non-existent connector"""
        result = ConnectorFactory.remove_connector("nonexistent")
        assert result == False
    
    def test_get_all_instances(self):
        """Test getting all instances"""
        conn1 = ConnectorFactory.create_connector(PlatformType.MT5, "test1")
        conn2 = ConnectorFactory.create_connector(PlatformType.MT5, "test2")
        
        instances = ConnectorFactory.get_all_instances()
        
        assert len(instances) == 2
        assert "test1" in instances
        assert "test2" in instances
        assert instances["test1"] is conn1
        assert instances["test2"] is conn2
    
    def test_get_all_instances_returns_copy(self):
        """Test that get_all_instances returns a copy"""
        ConnectorFactory.create_connector(PlatformType.MT5, "test1")
        instances = ConnectorFactory.get_all_instances()
        
        # Modify the copy
        from unittest.mock import Mock
        instances["test2"] = Mock()
        
        # Original should be unchanged
        assert ConnectorFactory.get_instance_count() == 1
        assert "test2" not in ConnectorFactory._instances
    
    def test_disconnect_all(self):
        """Test disconnecting all connectors"""
        ConnectorFactory.create_connector(PlatformType.MT5, "test1")
        ConnectorFactory.create_connector(PlatformType.MT5, "test2")
        
        ConnectorFactory.disconnect_all()
        
        assert ConnectorFactory.get_instance_count() == 0
    
    def test_get_instance_count(self):
        """Test getting instance count"""
        assert ConnectorFactory.get_instance_count() == 0
        
        ConnectorFactory.create_connector(PlatformType.MT5, "test1")
        assert ConnectorFactory.get_instance_count() == 1
        
        ConnectorFactory.create_connector(PlatformType.MT5, "test2")
        assert ConnectorFactory.get_instance_count() == 2
        
        ConnectorFactory.remove_connector("test1")
        assert ConnectorFactory.get_instance_count() == 1


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_create_mt5_connector_function(self):
        """Test create_mt5_connector convenience function"""
        connector = create_mt5_connector("test1")
        
        assert connector is not None
        assert isinstance(connector, MT5Connector)
    
    def test_create_mt4_connector_function(self):
        """Test create_mt4_connector convenience function"""
        connector = create_mt4_connector("test1")
        
        assert connector is not None
        assert isinstance(connector, MT4Connector)
    
    def test_create_mt5_connector_default_id(self):
        """Test create_mt5_connector with default ID"""
        connector = create_mt5_connector()
        
        assert connector is not None
        assert "default" in ConnectorFactory._instances
    
    def test_get_connector_function(self):
        """Test get_connector convenience function"""
        created = create_mt5_connector("test1")
        connector = get_connector("test1")
        
        assert connector is created
    
    def test_get_connector_function_nonexistent(self):
        """Test get_connector for non-existent instance"""
        connector = get_connector("nonexistent")
        assert connector is None
    
    def test_get_connector_function_default_id(self):
        """Test get_connector with default ID"""
        created = create_mt5_connector()  # Creates with default ID
        connector = get_connector()  # Gets with default ID
        
        assert connector is created


class TestFactoryStatePersistence:
    """Test factory state management"""
    
    def test_multiple_platform_instances(self):
        """Test creating instances of different platforms"""
        mt5_conn = ConnectorFactory.create_connector(PlatformType.MT5, "mt5_1")
        mt4_conn = ConnectorFactory.create_connector(PlatformType.MT4, "mt4_1")
        
        assert isinstance(mt5_conn, MT5Connector)
        assert isinstance(mt4_conn, MT4Connector)
        assert ConnectorFactory.get_instance_count() == 2
    
    def test_factory_state_isolated_between_ids(self):
        """Test that different instance IDs are properly isolated"""
        conn1 = ConnectorFactory.create_connector(PlatformType.MT5, "instance1")
        conn2 = ConnectorFactory.create_connector(PlatformType.MT5, "instance2")
        
        assert conn1 is not conn2
        assert ConnectorFactory.get_connector("instance1") is conn1
        assert ConnectorFactory.get_connector("instance2") is conn2
