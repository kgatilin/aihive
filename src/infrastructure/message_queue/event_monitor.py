"""
Event Monitoring and Logging Module

This module provides event monitoring and logging capabilities for tracking
events and messages across the asynchronous workflow.
"""

import logging
import json
import threading
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
import uuid
import os
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventLogEntry:
    """
    Represents a log entry for an event or command.
    """
    
    def __init__(self, message_type: str, message_id: str, correlation_id: Optional[str],
                 source: str, destination: Optional[str], payload: Dict[str, Any],
                 timestamp: Optional[datetime] = None, is_event: bool = True):
        """
        Initialize an event log entry.
        
        Args:
            message_type: Type of event or command
            message_id: Unique identifier for this message
            correlation_id: ID grouping related messages
            source: Component that generated the message
            destination: Target component (if applicable)
            payload: Message data
            timestamp: When the message was created
            is_event: True if this is an event, False if it's a command
        """
        self.message_type = message_type
        self.message_id = message_id
        self.correlation_id = correlation_id
        self.source = source
        self.destination = destination
        self.payload = payload
        self.timestamp = timestamp or datetime.now()
        self.is_event = is_event
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to a dictionary."""
        return {
            "message_type": self.message_type,
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "source": self.source,
            "destination": self.destination,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "is_event": self.is_event
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventLogEntry':
        """Create a log entry from a dictionary."""
        return cls(
            message_type=data["message_type"],
            message_id=data["message_id"],
            correlation_id=data.get("correlation_id"),
            source=data["source"],
            destination=data.get("destination"),
            payload=data["payload"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            is_event=data.get("is_event", True)
        )
    
    def __str__(self) -> str:
        """String representation of the log entry."""
        entry_type = "Event" if self.is_event else "Command"
        return (f"{entry_type} {self.message_type} from {self.source} "
                f"[{self.message_id}] @ {self.timestamp.isoformat()}")


class EventLogger:
    """
    Logger for events and commands.
    
    This class provides a centralized logging mechanism for
    events and commands passing through the message queue.
    """
    
    def __init__(self, log_directory: Optional[str] = None, 
                 max_memory_entries: int = 1000,
                 file_rotation_size: int = 10 * 1024 * 1024,  # 10 MB
                 enable_console_logging: bool = True):
        """
        Initialize the event logger.
        
        Args:
            log_directory: Directory to store log files
            max_memory_entries: Maximum number of entries to keep in memory
            file_rotation_size: Size in bytes at which to rotate log files
            enable_console_logging: Whether to log to console
        """
        self.log_entries: List[EventLogEntry] = []
        self.lock = threading.Lock()
        self.max_memory_entries = max_memory_entries
        self.file_rotation_size = file_rotation_size
        self.enable_console_logging = enable_console_logging
        
        # Set up log directory
        if log_directory:
            self.log_directory = Path(log_directory)
            self.log_directory.mkdir(parents=True, exist_ok=True)
            self.current_log_file = self._get_new_log_file()
        else:
            self.log_directory = None
            self.current_log_file = None
        
        logger.info(f"Initialized EventLogger with {'file logging' if log_directory else 'no file logging'}")
    
    def log_event(self, message_type: str, message_id: str, correlation_id: Optional[str],
                  source: str, payload: Dict[str, Any], destination: Optional[str] = None):
        """
        Log an event.
        
        Args:
            message_type: Type of event
            message_id: Unique identifier for this event
            correlation_id: ID grouping related events
            source: Component that generated the event
            payload: Event data
            destination: Target component (if applicable)
        """
        entry = EventLogEntry(
            message_type=message_type,
            message_id=message_id,
            correlation_id=correlation_id,
            source=source,
            destination=destination,
            payload=payload,
            is_event=True
        )
        
        self._store_entry(entry)
    
    def log_command(self, message_type: str, message_id: str, correlation_id: Optional[str],
                   source: str, destination: str, payload: Dict[str, Any]):
        """
        Log a command.
        
        Args:
            message_type: Type of command
            message_id: Unique identifier for this command
            correlation_id: ID grouping related commands
            source: Component that generated the command
            destination: Target component
            payload: Command data
        """
        entry = EventLogEntry(
            message_type=message_type,
            message_id=message_id,
            correlation_id=correlation_id,
            source=source,
            destination=destination,
            payload=payload,
            is_event=False
        )
        
        self._store_entry(entry)
    
    def _store_entry(self, entry: EventLogEntry):
        """
        Store a log entry.
        
        Args:
            entry: The log entry to store
        """
        with self.lock:
            # Add to in-memory storage
            self.log_entries.append(entry)
            
            # Trim if necessary
            if len(self.log_entries) > self.max_memory_entries:
                self.log_entries = self.log_entries[-self.max_memory_entries:]
            
            # Log to console if enabled
            if self.enable_console_logging:
                entry_type = "EVENT" if entry.is_event else "COMMAND"
                logger.info(f"{entry_type}: {entry.message_type} - {entry.message_id}")
            
            # Write to file if enabled
            if self.log_directory:
                self._write_to_file(entry)
    
    def _write_to_file(self, entry: EventLogEntry):
        """
        Write a log entry to file.
        
        Args:
            entry: The log entry to write
        """
        try:
            # Check if we need to rotate the log file
            if self.current_log_file and self.current_log_file.exists():
                if self.current_log_file.stat().st_size > self.file_rotation_size:
                    self.current_log_file = self._get_new_log_file()
            
            # Create file if it doesn't exist
            if not self.current_log_file:
                self.current_log_file = self._get_new_log_file()
            
            # Write entry to file
            with open(self.current_log_file, 'a') as f:
                json_entry = json.dumps(entry.to_dict())
                f.write(f"{json_entry}\n")
                
        except Exception as e:
            logger.error(f"Error writing to event log file: {e}")
    
    def _get_new_log_file(self) -> Path:
        """
        Get a new log file path.
        
        Returns:
            Path to a new log file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.log_directory / f"event_log_{timestamp}.jsonl"
    
    def get_recent_entries(self, count: int = 100) -> List[EventLogEntry]:
        """
        Get the most recent log entries.
        
        Args:
            count: Maximum number of entries to return
            
        Returns:
            List of recent log entries
        """
        with self.lock:
            return self.log_entries[-count:]
    
    def get_entries_by_correlation_id(self, correlation_id: str) -> List[EventLogEntry]:
        """
        Get log entries with a specific correlation ID.
        
        Args:
            correlation_id: Correlation ID to filter by
            
        Returns:
            List of matching log entries
        """
        with self.lock:
            return [entry for entry in self.log_entries if entry.correlation_id == correlation_id]
    
    def get_entries_by_type(self, message_type: str, is_event: bool = True) -> List[EventLogEntry]:
        """
        Get log entries of a specific type.
        
        Args:
            message_type: Message type to filter by
            is_event: True to filter events, False for commands
            
        Returns:
            List of matching log entries
        """
        with self.lock:
            return [
                entry for entry in self.log_entries 
                if entry.message_type == message_type and entry.is_event == is_event
            ]
    
    def clear_memory_logs(self):
        """Clear in-memory log entries."""
        with self.lock:
            self.log_entries.clear()


class EventMonitor:
    """
    Monitor for tracking event flow through the system.
    
    This class extends the event logger with real-time monitoring
    and notification capabilities.
    """
    
    def __init__(self, event_logger: EventLogger, alert_threshold_seconds: int = 60):
        """
        Initialize the event monitor.
        
        Args:
            event_logger: Logger for storing events
            alert_threshold_seconds: Threshold for timing alerts
        """
        self.event_logger = event_logger
        self.alert_threshold_seconds = alert_threshold_seconds
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_lock = threading.Lock()
        
        # Notification callbacks
        self.alert_callbacks: List[callable] = []
        
        # Start monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Started EventMonitor")
    
    def register_event(self, message_type: str, message_id: str, correlation_id: Optional[str],
                       source: str, payload: Dict[str, Any], destination: Optional[str] = None):
        """
        Register an event for monitoring.
        
        This both logs the event and updates workflow tracking.
        
        Args:
            message_type: Type of event
            message_id: Unique identifier for this event
            correlation_id: ID grouping related events
            source: Component that generated the event
            payload: Event data
            destination: Target component (if applicable)
        """
        # Log the event
        self.event_logger.log_event(
            message_type=message_type,
            message_id=message_id,
            correlation_id=correlation_id,
            source=source,
            payload=payload,
            destination=destination
        )
        
        # If there's a correlation ID, update workflow tracking
        if correlation_id:
            with self.workflow_lock:
                # Initialize workflow tracking if this is a new correlation ID
                if correlation_id not in self.active_workflows:
                    self.active_workflows[correlation_id] = {
                        "start_time": datetime.now(),
                        "events": [],
                        "last_update_time": datetime.now(),
                        "status": "active"
                    }
                
                # Update workflow tracking
                workflow = self.active_workflows[correlation_id]
                workflow["events"].append({
                    "message_type": message_type,
                    "message_id": message_id,
                    "source": source,
                    "timestamp": datetime.now().isoformat()
                })
                workflow["last_update_time"] = datetime.now()
                
                # Check for workflow completion events
                if self._is_completion_event(message_type):
                    workflow["status"] = "completed"
                    logger.info(f"Workflow {correlation_id} completed")
    
    def register_command(self, message_type: str, message_id: str, correlation_id: Optional[str],
                         source: str, destination: str, payload: Dict[str, Any]):
        """
        Register a command for monitoring.
        
        This both logs the command and updates workflow tracking.
        
        Args:
            message_type: Type of command
            message_id: Unique identifier for this command
            correlation_id: ID grouping related commands
            source: Component that generated the command
            destination: Target component
            payload: Command data
        """
        # Log the command
        self.event_logger.log_command(
            message_type=message_type,
            message_id=message_id,
            correlation_id=correlation_id,
            source=source,
            destination=destination,
            payload=payload
        )
        
        # If there's a correlation ID, update workflow tracking
        if correlation_id:
            with self.workflow_lock:
                # Initialize workflow tracking if this is a new correlation ID
                if correlation_id not in self.active_workflows:
                    self.active_workflows[correlation_id] = {
                        "start_time": datetime.now(),
                        "events": [],
                        "commands": [],
                        "last_update_time": datetime.now(),
                        "status": "active"
                    }
                
                # Update workflow tracking
                workflow = self.active_workflows[correlation_id]
                if "commands" not in workflow:
                    workflow["commands"] = []
                
                workflow["commands"].append({
                    "message_type": message_type,
                    "message_id": message_id,
                    "source": source,
                    "destination": destination,
                    "timestamp": datetime.now().isoformat()
                })
                workflow["last_update_time"] = datetime.now()
    
    def register_alert_callback(self, callback: callable):
        """
        Register a callback for alerts.
        
        Args:
            callback: Function to call when an alert is triggered
        """
        self.alert_callbacks.append(callback)
    
    def stop(self):
        """Stop the monitoring thread."""
        self.running = False
        self.monitor_thread.join(timeout=5)
        logger.info("Stopped EventMonitor")
    
    def get_workflow_status(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a workflow.
        
        Args:
            correlation_id: ID of the workflow
            
        Returns:
            Workflow status or None if not found
        """
        with self.workflow_lock:
            return self.active_workflows.get(correlation_id)
    
    def get_active_workflows(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active workflows.
        
        Returns:
            Dictionary of active workflows
        """
        with self.workflow_lock:
            return {
                cid: workflow
                for cid, workflow in self.active_workflows.items()
                if workflow["status"] == "active"
            }
    
    def _monitoring_loop(self):
        """Background thread for monitoring workflows."""
        while self.running:
            try:
                self._check_for_stalled_workflows()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Sleep before next check
            time.sleep(10)
    
    def _check_for_stalled_workflows(self):
        """Check for workflows that haven't been updated recently."""
        now = datetime.now()
        threshold = timedelta(seconds=self.alert_threshold_seconds)
        
        with self.workflow_lock:
            stalled_workflows = [
                (cid, workflow)
                for cid, workflow in self.active_workflows.items()
                if (workflow["status"] == "active" and 
                    now - workflow["last_update_time"] > threshold)
            ]
        
        # Alert for stalled workflows
        for cid, workflow in stalled_workflows:
            message = f"Workflow {cid} has not been updated in {self.alert_threshold_seconds} seconds"
            logger.warning(message)
            
            for callback in self.alert_callbacks:
                try:
                    callback({
                        "type": "stalled_workflow",
                        "correlation_id": cid,
                        "message": message,
                        "start_time": workflow["start_time"].isoformat(),
                        "last_update_time": workflow["last_update_time"].isoformat(),
                        "event_count": len(workflow.get("events", [])),
                        "command_count": len(workflow.get("commands", []))
                    })
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
    
    def _is_completion_event(self, message_type: str) -> bool:
        """
        Check if an event type indicates workflow completion.
        
        Args:
            message_type: Type of event
            
        Returns:
            True if this is a completion event, False otherwise
        """
        # Define event types that indicate workflow completion
        completion_events = {
            "TASK_COMPLETED",
            "WORKFLOW_COMPLETED",
            "PRD_APPROVED"
        }
        
        return message_type in completion_events


def create_event_monitoring_system(log_directory: Optional[str] = None, 
                                  max_memory_entries: int = 1000,
                                  alert_threshold_seconds: int = 60) -> EventMonitor:
    """
    Factory function to create an EventMonitor.
    
    Args:
        log_directory: Directory to store log files
        max_memory_entries: Maximum number of entries to keep in memory
        alert_threshold_seconds: Threshold for timing alerts
        
    Returns:
        A configured EventMonitor instance
    """
    # Create default log directory if not specified
    if not log_directory:
        app_dir = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
        log_directory = os.path.join(app_dir, "logs", "events")
    
    # Create event logger
    event_logger = EventLogger(
        log_directory=log_directory,
        max_memory_entries=max_memory_entries
    )
    
    # Create event monitor
    return EventMonitor(
        event_logger=event_logger,
        alert_threshold_seconds=alert_threshold_seconds
    ) 