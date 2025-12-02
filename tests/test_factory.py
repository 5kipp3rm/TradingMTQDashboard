"""
Tests for connector factory
"""
import pytest
from src.connectors.factory import ConnectorFactory, create_mt5_connector
from src.connectors.base import PlatformType
from src.connectors.mt5_connector import MT5Connector
from src.connectors.mt4_connector import MT4Connector


def test_create_mt5_connector():
    """Test creating MT5 connector"""
    connector = ConnectorFactory.create_connector(PlatformType.MT5, "test_mt5")
    
    assert connector is not None
    assert isinstance(connector, MT5Connector)
    assert connector.get_instance_id() == "test_mt5"
    assert connector.get_platform_type() == PlatformType.MT5
    
    # Cleanup
    ConnectorFactory.remove_connector("test_mt5")


def test_create_mt4_connector():
    """Test creating MT4 connector"""
    connector = ConnectorFactory.create_connector(PlatformType.MT4, "test_mt4")
    
    assert connector is not None
    assert isinstance(connector, MT4Connector)
    assert connector.get_instance_id() == "test_mt4"
    assert connector.get_platform_type() == PlatformType.MT4
    
    # Cleanup
    ConnectorFactory.remove_connector("test_mt4")


def test_multiple_instances():
    """Test creating multiple connector instances"""
    conn1 = ConnectorFactory.create_connector(PlatformType.MT5, "instance1")
    conn2 = ConnectorFactory.create_connector(PlatformType.MT5, "instance2")
    
    assert conn1.get_instance_id() == "instance1"
    assert conn2.get_instance_id() == "instance2"
    assert conn1 is not conn2
    
    # Cleanup
    ConnectorFactory.disconnect_all()
    assert ConnectorFactory.get_instance_count() == 0


def test_get_connector():
    """Test getting existing connector"""
    ConnectorFactory.create_connector(PlatformType.MT5, "test")
    
    connector = ConnectorFactory.get_connector("test")
    assert connector is not None
    assert connector.get_instance_id() == "test"
    
    # Non-existent connector
    assert ConnectorFactory.get_connector("nonexistent") is None
    
    # Cleanup
    ConnectorFactory.disconnect_all()


def test_remove_connector():
    """Test removing connector"""
    ConnectorFactory.create_connector(PlatformType.MT5, "test")
    
    assert ConnectorFactory.get_instance_count() == 1
    
    result = ConnectorFactory.remove_connector("test")
    assert result is True
    assert ConnectorFactory.get_instance_count() == 0
    
    # Removing non-existent
    result = ConnectorFactory.remove_connector("nonexistent")
    assert result is False


def test_disconnect_all():
    """Test disconnecting all connectors"""
    ConnectorFactory.create_connector(PlatformType.MT5, "inst1")
    ConnectorFactory.create_connector(PlatformType.MT5, "inst2")
    ConnectorFactory.create_connector(PlatformType.MT5, "inst3")
    
    assert ConnectorFactory.get_instance_count() == 3
    
    ConnectorFactory.disconnect_all()
    assert ConnectorFactory.get_instance_count() == 0


def test_convenience_function():
    """Test convenience function for creating MT5 connector"""
    connector = create_mt5_connector("convenience")
    
    assert connector is not None
    assert isinstance(connector, MT5Connector)
    assert connector.get_instance_id() == "convenience"
    
    # Cleanup
    ConnectorFactory.disconnect_all()


# Cleanup after all tests
@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup after each test"""
    yield
    ConnectorFactory.disconnect_all()
