import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from src.core.domain_events.base_event import DomainEvent
from src.core.message_broker.infrastructure.in_memory_broker import InMemoryBroker


@pytest.fixture
def broker():
    """Create an InMemoryBroker instance for testing."""
    return InMemoryBroker()


@pytest.fixture
def sample_event():
    """Create a sample domain event for testing."""
    return DomainEvent(
        event_id="test-event-123",
        event_type="test.event",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
        aggregate_id="test-aggregate-123"
    )


class TestInMemoryBroker:
    """Test suite for the InMemoryBroker."""

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, broker):
        """Test connecting and disconnecting from the broker."""
        assert not broker.is_connected
        
        await broker.connect()
        assert broker.is_connected
        
        await broker.disconnect()
        assert not broker.is_connected

    @pytest.mark.asyncio
    async def test_publish_event_without_subscribers(self, broker, sample_event):
        """Test publishing an event with no subscribers."""
        await broker.connect()
        await broker.publish_event(sample_event)
        # No assertions needed, just verify it doesn't raise exceptions

    @pytest.mark.asyncio
    async def test_publish_event_with_subscribers(self, broker, sample_event):
        """Test publishing an event with subscribers."""
        await broker.connect()
        
        # Create mock subscribers
        mock_callback1 = AsyncMock()
        mock_callback2 = AsyncMock()
        
        # Subscribe to events
        await broker.subscribe_to_event("test.event", mock_callback1)
        await broker.subscribe_to_event("test.event", mock_callback2)
        
        # Publish event
        await broker.publish_event(sample_event)
        
        # Verify callbacks were called
        mock_callback1.assert_called_once_with(sample_event)
        mock_callback2.assert_called_once_with(sample_event)

    @pytest.mark.asyncio
    async def test_publish_command_without_subscribers(self, broker):
        """Test publishing a command with no subscribers."""
        await broker.connect()
        await broker.publish_command("test.command", {"key": "value"})
        # No assertions needed, just verify it doesn't raise exceptions

    @pytest.mark.asyncio
    async def test_publish_command_with_subscribers(self, broker):
        """Test publishing a command with subscribers."""
        await broker.connect()
        
        # Create mock subscribers
        mock_callback1 = AsyncMock()
        mock_callback2 = AsyncMock()
        
        # Subscribe to commands
        await broker.subscribe_to_command("test.command", mock_callback1)
        await broker.subscribe_to_command("test.command", mock_callback2)
        
        # Publish command
        command_payload = {"key": "value"}
        await broker.publish_command("test.command", command_payload)
        
        # Verify callbacks were called
        mock_callback1.assert_called_once_with(command_payload)
        mock_callback2.assert_called_once_with(command_payload)

    @pytest.mark.asyncio
    async def test_operations_without_connection(self, broker, sample_event):
        """Test that operations fail when not connected."""
        with pytest.raises(RuntimeError):
            await broker.publish_event(sample_event)
        
        with pytest.raises(RuntimeError):
            await broker.subscribe_to_event("test.event", AsyncMock())
        
        with pytest.raises(RuntimeError):
            await broker.publish_command("test.command", {"key": "value"})
        
        with pytest.raises(RuntimeError):
            await broker.subscribe_to_command("test.command", AsyncMock()) 