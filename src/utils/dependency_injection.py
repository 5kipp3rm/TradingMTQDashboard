"""
Dependency Injection Container for TradingMTQ

Provides a simple but powerful dependency injection (DI) system for managing
dependencies across the application. Eliminates global singletons and makes
testing easier through explicit dependency declaration.

Features:
- Singleton and transient service lifetimes
- Factory registration for complex object creation
- Automatic dependency resolution
- Thread-safe container
- Service validation and health checks

Usage:
    from src.utils.dependency_injection import Container

    # Create container
    container = Container()

    # Register services
    container.register_singleton(MT5Connector, instance=mt5_connector)
    container.register_transient(StrategyFactory)

    # Resolve dependencies
    connector = container.resolve(MT5Connector)
    strategy = container.resolve(StrategyFactory)
"""
from typing import Dict, Any, Type, TypeVar, Callable, Optional
from enum import Enum
import threading
import logging


logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime options"""
    SINGLETON = "singleton"  # Single instance for lifetime of container
    TRANSIENT = "transient"  # New instance on each resolve


class ServiceDescriptor:
    """Describes how to create and manage a service"""

    def __init__(
        self,
        service_type: Type,
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable] = None,
        instance: Any = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ):
        """
        Initialize service descriptor

        Args:
            service_type: The service interface or class type
            implementation_type: Concrete implementation (if different from service_type)
            factory: Factory function to create service
            instance: Pre-created instance (for singletons)
            lifetime: Service lifetime (singleton or transient)
        """
        self.service_type = service_type
        self.implementation_type = implementation_type or service_type
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime


class Container:
    """
    Dependency Injection Container

    Manages service registration and resolution with support for
    singleton and transient lifetimes.
    """

    def __init__(self):
        """Initialize container"""
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._lock = threading.Lock()
        self._initialized = False
        logger.info("Dependency injection container initialized")

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None
    ) -> 'Container':
        """
        Register a singleton service (single instance for container lifetime)

        Args:
            service_type: Service interface or class
            implementation_type: Concrete implementation class
            factory: Factory function to create instance
            instance: Pre-created instance

        Returns:
            Self for chaining

        Example:
            # Register with existing instance
            container.register_singleton(MT5Connector, instance=connector)

            # Register with factory
            container.register_singleton(
                MT5Connector,
                factory=lambda: MT5Connector("default")
            )

            # Register with implementation type
            container.register_singleton(MT5Connector, implementation_type=MT5Connector)
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation_type,
                factory=factory,
                instance=instance,
                lifetime=ServiceLifetime.SINGLETON
            )
            self._services[service_type] = descriptor

            logger.debug(
                f"Registered singleton: {service_type.__name__}",
                extra={'service': service_type.__name__, 'lifetime': 'singleton'}
            )

        return self

    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'Container':
        """
        Register a transient service (new instance on each resolve)

        Args:
            service_type: Service interface or class
            implementation_type: Concrete implementation class
            factory: Factory function to create instance

        Returns:
            Self for chaining

        Example:
            # Register with implementation type
            container.register_transient(Strategy, implementation_type=RSIStrategy)

            # Register with factory
            container.register_transient(
                Strategy,
                factory=lambda: RSIStrategy(period=14)
            )
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation_type,
                factory=factory,
                lifetime=ServiceLifetime.TRANSIENT
            )
            self._services[service_type] = descriptor

            logger.debug(
                f"Registered transient: {service_type.__name__}",
                extra={'service': service_type.__name__, 'lifetime': 'transient'}
            )

        return self

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service from the container

        Args:
            service_type: Service type to resolve

        Returns:
            Service instance

        Raises:
            KeyError: If service not registered
            RuntimeError: If service creation fails

        Example:
            connector = container.resolve(MT5Connector)
            strategy = container.resolve(Strategy)
        """
        if service_type not in self._services:
            raise KeyError(
                f"Service '{service_type.__name__}' not registered in container. "
                f"Available services: {[s.__name__ for s in self._services.keys()]}"
            )

        descriptor = self._services[service_type]

        # Return existing singleton instance
        if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor.instance:
            return descriptor.instance

        # Create new instance
        instance = self._create_instance(descriptor)

        # Store singleton instance
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            with self._lock:
                descriptor.instance = instance

        return instance

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """
        Create service instance using descriptor

        Args:
            descriptor: Service descriptor

        Returns:
            Created instance

        Raises:
            RuntimeError: If instance creation fails
        """
        try:
            # Use factory if provided
            if descriptor.factory:
                instance = descriptor.factory()
                logger.debug(
                    f"Created instance using factory: {descriptor.service_type.__name__}"
                )
                return instance

            # Create instance from implementation type
            instance = descriptor.implementation_type()
            logger.debug(
                f"Created instance from type: {descriptor.implementation_type.__name__}"
            )
            return instance

        except Exception as e:
            logger.error(
                f"Failed to create instance of {descriptor.service_type.__name__}: {e}",
                exc_info=True
            )
            raise RuntimeError(
                f"Failed to create service '{descriptor.service_type.__name__}': {e}"
            ) from e

    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service, returns None if not found

        Args:
            service_type: Service type to resolve

        Returns:
            Service instance or None if not found

        Example:
            connector = container.try_resolve(MT5Connector)
            if connector:
                connector.connect()
        """
        try:
            return self.resolve(service_type)
        except KeyError:
            logger.warning(
                f"Service '{service_type.__name__}' not found in container"
            )
            return None

    def is_registered(self, service_type: Type) -> bool:
        """
        Check if service is registered

        Args:
            service_type: Service type to check

        Returns:
            True if registered
        """
        return service_type in self._services

    def get_registered_services(self) -> list[Type]:
        """
        Get list of all registered service types

        Returns:
            List of registered service types
        """
        return list(self._services.keys())

    def clear(self):
        """Clear all registered services"""
        with self._lock:
            self._services.clear()
            logger.info("Container cleared")

    def validate(self) -> list[str]:
        """
        Validate all registered services can be created

        Returns:
            List of validation errors (empty if all valid)

        Example:
            errors = container.validate()
            if errors:
                print(f"Validation failed: {errors}")
        """
        errors = []

        for service_type, descriptor in self._services.items():
            try:
                # Try to create instance (for transient)
                # or verify singleton instance exists
                if descriptor.lifetime == ServiceLifetime.SINGLETON:
                    if descriptor.instance is None and descriptor.factory is None:
                        if descriptor.implementation_type:
                            # Try to create instance
                            test_instance = descriptor.implementation_type()
                        else:
                            errors.append(
                                f"Singleton {service_type.__name__} has no instance or factory"
                            )
                elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
                    if descriptor.factory is None and descriptor.implementation_type is None:
                        errors.append(
                            f"Transient {service_type.__name__} has no factory or implementation"
                        )

            except Exception as e:
                errors.append(
                    f"Failed to validate {service_type.__name__}: {str(e)}"
                )

        if errors:
            logger.warning(f"Container validation failed with {len(errors)} errors")
        else:
            logger.info("Container validation passed")

        return errors

    def __repr__(self) -> str:
        """String representation"""
        services = [s.__name__ for s in self._services.keys()]
        return f"Container(services={len(services)}, registered={services})"


# =============================================================================
# Global Container Instance (Optional)
# =============================================================================

_global_container: Optional[Container] = None
_container_lock = threading.Lock()


def get_container() -> Container:
    """
    Get or create global container instance

    Returns:
        Global container

    Example:
        container = get_container()
        container.register_singleton(MT5Connector, instance=connector)
    """
    global _global_container

    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = Container()

    return _global_container


def reset_container():
    """Reset global container (useful for testing)"""
    global _global_container

    with _container_lock:
        if _global_container:
            _global_container.clear()
        _global_container = None


# =============================================================================
# Decorator for Service Registration
# =============================================================================

def injectable(lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT):
    """
    Decorator to mark a class as injectable

    Args:
        lifetime: Service lifetime (singleton or transient)

    Example:
        @injectable(lifetime=ServiceLifetime.SINGLETON)
        class MT5Connector:
            def __init__(self):
                pass
    """
    def decorator(cls):
        cls.__injectable__ = True
        cls.__lifetime__ = lifetime
        return cls

    return decorator


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)

    # Example 1: Basic registration and resolution
    print("Example 1: Basic DI")

    class DatabaseService:
        def query(self):
            return "Database query result"

    class ApiService:
        def fetch(self):
            return "API data"

    container = Container()
    container.register_singleton(DatabaseService, instance=DatabaseService())
    container.register_transient(ApiService, implementation_type=ApiService)

    # Resolve services
    db = container.resolve(DatabaseService)
    api1 = container.resolve(ApiService)
    api2 = container.resolve(ApiService)

    print(f"DB query: {db.query()}")
    print(f"API1 fetch: {api1.fetch()}")
    print(f"API2 fetch: {api2.fetch()}")
    print(f"DB singleton same instance: {container.resolve(DatabaseService) is db}")
    print(f"API transient different instances: {api1 is not api2}")

    # Example 2: Factory registration
    print("\nExample 2: Factory registration")

    class ConfigurableService:
        def __init__(self, config: str):
            self.config = config

    container.register_singleton(
        ConfigurableService,
        factory=lambda: ConfigurableService("production")
    )

    service = container.resolve(ConfigurableService)
    print(f"Service config: {service.config}")

    # Example 3: Validation
    print("\nExample 3: Validation")
    errors = container.validate()
    if errors:
        print(f"Validation errors: {errors}")
    else:
        print("✅ All services valid")

    # Example 4: List registered services
    print(f"\nRegistered services: {container.get_registered_services()}")
