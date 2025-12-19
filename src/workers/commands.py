"""
Worker Commands - Command Pattern Implementation

Defines concrete commands for worker operations.

Design Pattern: Command Pattern
- Encapsulates requests as objects
- Allows parameterization of clients with different requests
- Enables queuing, logging, and undo operations

SOLID: Single Responsibility - each command has one purpose
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from src.workers.interfaces import ICommand


@dataclass
class ConnectCommand(ICommand):
    """
    Command to connect worker to MT5 terminal

    Encapsulates connection parameters.
    """
    login: int
    password: str
    server: str
    timeout: int = 60000
    portable: bool = False

    def get_type(self) -> str:
        return "connect"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "login": self.login,
            "password": self.password,
            "server": self.server,
            "timeout": self.timeout,
            "portable": self.portable,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectCommand':
        return cls(
            login=data["login"],
            password=data["password"],
            server=data["server"],
            timeout=data.get("timeout", 60000),
            portable=data.get("portable", False),
        )


@dataclass
class DisconnectCommand(ICommand):
    """Command to disconnect worker from MT5 terminal"""

    def get_type(self) -> str:
        return "disconnect"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.get_type()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DisconnectCommand':
        return cls()


@dataclass
class ExecuteTradingCycleCommand(ICommand):
    """
    Command to execute one trading cycle

    Runs strategy analysis, signal generation, and trade execution.
    """
    currency_symbols: Optional[list[str]] = None
    force_check: bool = False

    def get_type(self) -> str:
        return "execute_trading_cycle"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "currency_symbols": self.currency_symbols,
            "force_check": self.force_check,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecuteTradingCycleCommand':
        return cls(
            currency_symbols=data.get("currency_symbols"),
            force_check=data.get("force_check", False),
        )


@dataclass
class GetAccountInfoCommand(ICommand):
    """Command to retrieve account information"""

    def get_type(self) -> str:
        return "get_account_info"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.get_type()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GetAccountInfoCommand':
        return cls()


@dataclass
class GetPositionsCommand(ICommand):
    """Command to retrieve current positions"""
    symbol: Optional[str] = None  # Filter by symbol (optional)

    def get_type(self) -> str:
        return "get_positions"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "symbol": self.symbol,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GetPositionsCommand':
        return cls(symbol=data.get("symbol"))


@dataclass
class PlaceOrderCommand(ICommand):
    """Command to place a trading order"""
    symbol: str
    order_type: str
    volume: float
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    comment: str = ""
    magic_number: int = 0

    def get_type(self) -> str:
        return "place_order"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "symbol": self.symbol,
            "order_type": self.order_type,
            "volume": self.volume,
            "price": self.price,
            "sl": self.sl,
            "tp": self.tp,
            "comment": self.comment,
            "magic_number": self.magic_number,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaceOrderCommand':
        return cls(
            symbol=data["symbol"],
            order_type=data["order_type"],
            volume=data["volume"],
            price=data.get("price"),
            sl=data.get("sl"),
            tp=data.get("tp"),
            comment=data.get("comment", ""),
            magic_number=data.get("magic_number", 0),
        )


@dataclass
class ModifyPositionCommand(ICommand):
    """Command to modify existing position (SL/TP)"""
    ticket: int
    sl: Optional[float] = None
    tp: Optional[float] = None

    def get_type(self) -> str:
        return "modify_position"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "ticket": self.ticket,
            "sl": self.sl,
            "tp": self.tp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModifyPositionCommand':
        return cls(
            ticket=data["ticket"],
            sl=data.get("sl"),
            tp=data.get("tp"),
        )


@dataclass
class ClosePositionCommand(ICommand):
    """Command to close position"""
    ticket: int
    volume: Optional[float] = None  # Partial close if specified

    def get_type(self) -> str:
        return "close_position"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "ticket": self.ticket,
            "volume": self.volume,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClosePositionCommand':
        return cls(
            ticket=data["ticket"],
            volume=data.get("volume"),
        )


@dataclass
class GetHistoryCommand(ICommand):
    """Command to retrieve historical data"""
    symbol: str
    timeframe: str
    bars: int = 100
    start_time: Optional[str] = None  # ISO format datetime

    def get_type(self) -> str:
        return "get_history"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "bars": self.bars,
            "start_time": self.start_time,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GetHistoryCommand':
        return cls(
            symbol=data["symbol"],
            timeframe=data["timeframe"],
            bars=data.get("bars", 100),
            start_time=data.get("start_time"),
        )


@dataclass
class HealthCheckCommand(ICommand):
    """Command to check worker health"""

    def get_type(self) -> str:
        return "health_check"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.get_type()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthCheckCommand':
        return cls()


class CommandFactory:
    """
    Factory for creating commands from dictionary representation

    Design Pattern: Factory Pattern
    - Centralizes command creation logic
    - Maps command types to command classes

    SOLID: Open/Closed - easy to add new command types
    """

    _command_registry: Dict[str, type[ICommand]] = {
        "connect": ConnectCommand,
        "disconnect": DisconnectCommand,
        "execute_trading_cycle": ExecuteTradingCycleCommand,
        "get_account_info": GetAccountInfoCommand,
        "get_positions": GetPositionsCommand,
        "place_order": PlaceOrderCommand,
        "modify_position": ModifyPositionCommand,
        "close_position": ClosePositionCommand,
        "get_history": GetHistoryCommand,
        "health_check": HealthCheckCommand,
    }

    @classmethod
    def create_command(cls, data: Dict[str, Any]) -> ICommand:
        """
        Create command from dictionary

        Args:
            data: Command data with 'type' field

        Returns:
            Command instance

        Raises:
            ValueError: If command type is unknown
        """
        command_type = data.get("type")
        if not command_type:
            raise ValueError("Command data must contain 'type' field")

        command_class = cls._command_registry.get(command_type)
        if not command_class:
            raise ValueError(f"Unknown command type: {command_type}")

        return command_class.from_dict(data)

    @classmethod
    def register_command(cls, command_type: str, command_class: type[ICommand]) -> None:
        """
        Register new command type

        Args:
            command_type: Command type identifier
            command_class: Command class

        Notes:
            Allows extending the system with custom commands
        """
        cls._command_registry[command_type] = command_class

    @classmethod
    def get_supported_commands(cls) -> list[str]:
        """
        Get list of supported command types

        Returns:
            List of command type identifiers
        """
        return list(cls._command_registry.keys())
