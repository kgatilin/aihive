from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Awaitable, Optional

from src.core.domain_events.base_event import DomainEvent


class MessageBroker(ABC):
    """Abstract interface for message broker implementations."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the message broker."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the message broker."""
        pass
    
    @abstractmethod
    async def publish_event(self, event: DomainEvent) -> None:
        """Publish a domain event to the event exchange."""
        pass
    
    @abstractmethod
    async def subscribe_to_event(
        self, 
        event_type: str, 
        callback: Callable[[DomainEvent], Awaitable[None]],
        queue_name: Optional[str] = None
    ) -> None:
        """Subscribe to a specific event type with a callback function."""
        pass
    
    @abstractmethod
    async def publish_command(self, command_type: str, payload: Dict[str, Any]) -> None:
        """Publish a command to the command exchange."""
        pass
    
    @abstractmethod
    async def subscribe_to_command(
        self,
        command_type: str,
        callback: Callable[[Dict[str, Any]], Awaitable[None]],
        queue_name: Optional[str] = None
    ) -> None:
        """Subscribe to a specific command type with a callback function."""
        pass 