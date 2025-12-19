"""
Unit tests for Worker Commands

Tests Command Pattern implementation and serialization.
"""

import pytest
from src.workers.commands import (
    ConnectCommand,
    DisconnectCommand,
    ExecuteTradingCycleCommand,
    GetAccountInfoCommand,
    GetPositionsCommand,
    PlaceOrderCommand,
    ModifyPositionCommand,
    ClosePositionCommand,
    GetHistoryCommand,
    HealthCheckCommand,
    CommandFactory,
)


class TestConnectCommand:
    """Tests for ConnectCommand"""

    def test_create_connect_command(self):
        """Test creating connect command"""
        cmd = ConnectCommand(
            login=12345,
            password="secret",
            server="Broker-Server",
            timeout=60000,
            portable=False
        )

        assert cmd.login == 12345
        assert cmd.password == "secret"
        assert cmd.server == "Broker-Server"
        assert cmd.timeout == 60000
        assert cmd.portable is False

    def test_connect_command_type(self):
        """Test command type"""
        cmd = ConnectCommand(login=12345, password="secret", server="Broker-Server")
        assert cmd.get_type() == "connect"

    def test_connect_command_to_dict(self):
        """Test serialization to dictionary"""
        cmd = ConnectCommand(
            login=12345,
            password="secret",
            server="Broker-Server",
            timeout=60000,
            portable=True
        )

        data = cmd.to_dict()

        assert data["type"] == "connect"
        assert data["login"] == 12345
        assert data["password"] == "secret"
        assert data["server"] == "Broker-Server"
        assert data["timeout"] == 60000
        assert data["portable"] is True

    def test_connect_command_from_dict(self):
        """Test deserialization from dictionary"""
        data = {
            "type": "connect",
            "login": 12345,
            "password": "secret",
            "server": "Broker-Server",
            "timeout": 60000,
            "portable": True
        }

        cmd = ConnectCommand.from_dict(data)

        assert cmd.login == 12345
        assert cmd.password == "secret"
        assert cmd.server == "Broker-Server"
        assert cmd.timeout == 60000
        assert cmd.portable is True

    def test_connect_command_defaults(self):
        """Test default values"""
        data = {
            "login": 12345,
            "password": "secret",
            "server": "Broker-Server"
        }

        cmd = ConnectCommand.from_dict(data)

        assert cmd.timeout == 60000  # Default
        assert cmd.portable is False  # Default


class TestDisconnectCommand:
    """Tests for DisconnectCommand"""

    def test_disconnect_command(self):
        """Test disconnect command"""
        cmd = DisconnectCommand()
        assert cmd.get_type() == "disconnect"

    def test_disconnect_command_serialization(self):
        """Test serialization roundtrip"""
        cmd = DisconnectCommand()
        data = cmd.to_dict()

        assert data["type"] == "disconnect"

        cmd2 = DisconnectCommand.from_dict(data)
        assert cmd2.get_type() == "disconnect"


class TestExecuteTradingCycleCommand:
    """Tests for ExecuteTradingCycleCommand"""

    def test_trading_cycle_command(self):
        """Test trading cycle command"""
        cmd = ExecuteTradingCycleCommand(
            currency_symbols=["EURUSD", "GBPUSD"],
            force_check=True
        )

        assert cmd.currency_symbols == ["EURUSD", "GBPUSD"]
        assert cmd.force_check is True

    def test_trading_cycle_command_defaults(self):
        """Test default values"""
        cmd = ExecuteTradingCycleCommand()

        assert cmd.currency_symbols is None
        assert cmd.force_check is False

    def test_trading_cycle_serialization(self):
        """Test serialization roundtrip"""
        cmd = ExecuteTradingCycleCommand(
            currency_symbols=["EURUSD"],
            force_check=True
        )

        data = cmd.to_dict()
        cmd2 = ExecuteTradingCycleCommand.from_dict(data)

        assert cmd2.currency_symbols == ["EURUSD"]
        assert cmd2.force_check is True


class TestPlaceOrderCommand:
    """Tests for PlaceOrderCommand"""

    def test_place_order_command(self):
        """Test place order command"""
        cmd = PlaceOrderCommand(
            symbol="EURUSD",
            order_type="BUY",
            volume=0.1,
            price=1.2000,
            sl=1.1950,
            tp=1.2100,
            comment="Test order",
            magic_number=12345
        )

        assert cmd.symbol == "EURUSD"
        assert cmd.order_type == "BUY"
        assert cmd.volume == 0.1
        assert cmd.price == 1.2000
        assert cmd.sl == 1.1950
        assert cmd.tp == 1.2100
        assert cmd.comment == "Test order"
        assert cmd.magic_number == 12345

    def test_place_order_serialization(self):
        """Test serialization roundtrip"""
        cmd = PlaceOrderCommand(
            symbol="EURUSD",
            order_type="BUY",
            volume=0.1
        )

        data = cmd.to_dict()
        cmd2 = PlaceOrderCommand.from_dict(data)

        assert cmd2.symbol == "EURUSD"
        assert cmd2.order_type == "BUY"
        assert cmd2.volume == 0.1


class TestModifyPositionCommand:
    """Tests for ModifyPositionCommand"""

    def test_modify_position_command(self):
        """Test modify position command"""
        cmd = ModifyPositionCommand(
            ticket=123456,
            sl=1.1950,
            tp=1.2100
        )

        assert cmd.ticket == 123456
        assert cmd.sl == 1.1950
        assert cmd.tp == 1.2100

    def test_modify_position_serialization(self):
        """Test serialization roundtrip"""
        cmd = ModifyPositionCommand(ticket=123456, sl=1.1950)

        data = cmd.to_dict()
        cmd2 = ModifyPositionCommand.from_dict(data)

        assert cmd2.ticket == 123456
        assert cmd2.sl == 1.1950


class TestClosePositionCommand:
    """Tests for ClosePositionCommand"""

    def test_close_position_command(self):
        """Test close position command"""
        cmd = ClosePositionCommand(ticket=123456, volume=0.05)

        assert cmd.ticket == 123456
        assert cmd.volume == 0.05

    def test_close_position_full_close(self):
        """Test full position close (no volume specified)"""
        cmd = ClosePositionCommand(ticket=123456)

        assert cmd.ticket == 123456
        assert cmd.volume is None  # Full close


class TestGetHistoryCommand:
    """Tests for GetHistoryCommand"""

    def test_get_history_command(self):
        """Test get history command"""
        cmd = GetHistoryCommand(
            symbol="EURUSD",
            timeframe="H1",
            bars=100,
            start_time="2025-01-01T00:00:00"
        )

        assert cmd.symbol == "EURUSD"
        assert cmd.timeframe == "H1"
        assert cmd.bars == 100
        assert cmd.start_time == "2025-01-01T00:00:00"

    def test_get_history_defaults(self):
        """Test default values"""
        cmd = GetHistoryCommand(symbol="EURUSD", timeframe="H1")

        assert cmd.bars == 100  # Default
        assert cmd.start_time is None


class TestCommandFactory:
    """Tests for CommandFactory"""

    def test_factory_create_connect_command(self):
        """Test factory creates connect command"""
        data = {
            "type": "connect",
            "login": 12345,
            "password": "secret",
            "server": "Broker-Server"
        }

        cmd = CommandFactory.create_command(data)

        assert isinstance(cmd, ConnectCommand)
        assert cmd.login == 12345

    def test_factory_create_all_command_types(self):
        """Test factory creates all command types"""
        commands = [
            ({"type": "connect", "login": 1, "password": "p", "server": "s"}, ConnectCommand),
            ({"type": "disconnect"}, DisconnectCommand),
            ({"type": "execute_trading_cycle"}, ExecuteTradingCycleCommand),
            ({"type": "get_account_info"}, GetAccountInfoCommand),
            ({"type": "get_positions"}, GetPositionsCommand),
            ({"type": "place_order", "symbol": "EURUSD", "order_type": "BUY", "volume": 0.1}, PlaceOrderCommand),
            ({"type": "modify_position", "ticket": 123}, ModifyPositionCommand),
            ({"type": "close_position", "ticket": 123}, ClosePositionCommand),
            ({"type": "get_history", "symbol": "EURUSD", "timeframe": "H1"}, GetHistoryCommand),
            ({"type": "health_check"}, HealthCheckCommand),
        ]

        for data, expected_type in commands:
            cmd = CommandFactory.create_command(data)
            assert isinstance(cmd, expected_type)

    def test_factory_unknown_command_type(self):
        """Test factory raises error for unknown command type"""
        with pytest.raises(ValueError, match="Unknown command type"):
            CommandFactory.create_command({"type": "unknown_command"})

    def test_factory_missing_type_field(self):
        """Test factory raises error for missing type field"""
        with pytest.raises(ValueError, match="Command data must contain 'type' field"):
            CommandFactory.create_command({"login": 12345})

    def test_factory_get_supported_commands(self):
        """Test getting list of supported commands"""
        commands = CommandFactory.get_supported_commands()

        assert "connect" in commands
        assert "disconnect" in commands
        assert "execute_trading_cycle" in commands
        assert "get_account_info" in commands
        assert "place_order" in commands
        assert len(commands) == 10  # All commands

    def test_factory_register_custom_command(self):
        """Test registering custom command type"""
        from dataclasses import dataclass
        from src.workers.interfaces import ICommand

        @dataclass
        class CustomCommand(ICommand):
            value: int

            def get_type(self) -> str:
                return "custom"

            def to_dict(self):
                return {"type": "custom", "value": self.value}

            @classmethod
            def from_dict(cls, data):
                return cls(value=data["value"])

        # Register custom command
        CommandFactory.register_command("custom", CustomCommand)

        # Create custom command via factory
        cmd = CommandFactory.create_command({"type": "custom", "value": 42})

        assert isinstance(cmd, CustomCommand)
        assert cmd.value == 42


class TestCommandSerialization:
    """Tests for command serialization/deserialization"""

    def test_all_commands_serialize_deserialize(self):
        """Test all commands can be serialized and deserialized"""
        commands = [
            ConnectCommand(login=1, password="p", server="s"),
            DisconnectCommand(),
            ExecuteTradingCycleCommand(currency_symbols=["EURUSD"]),
            GetAccountInfoCommand(),
            GetPositionsCommand(symbol="EURUSD"),
            PlaceOrderCommand(symbol="EURUSD", order_type="BUY", volume=0.1),
            ModifyPositionCommand(ticket=123, sl=1.0),
            ClosePositionCommand(ticket=123),
            GetHistoryCommand(symbol="EURUSD", timeframe="H1"),
            HealthCheckCommand(),
        ]

        for original_cmd in commands:
            # Serialize
            data = original_cmd.to_dict()

            # Deserialize via factory
            restored_cmd = CommandFactory.create_command(data)

            # Verify type matches
            assert type(restored_cmd) == type(original_cmd)
            assert restored_cmd.get_type() == original_cmd.get_type()
