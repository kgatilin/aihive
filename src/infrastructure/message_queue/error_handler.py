"""
Error Handler for Message Queue

This module provides error handling and recovery mechanisms for the message queue.
"""

import logging
import time
import json
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MessageProcessingError(Exception):
    """Exception raised for errors in message processing."""
    
    def __init__(self, message: str, message_data: Dict[str, Any], error: Exception, retryable: bool = True):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            message_data: The message data that caused the error
            error: The original exception
            retryable: Whether the error is retryable
        """
        self.message_data = message_data
        self.original_error = error
        self.retryable = retryable
        self.timestamp = datetime.now()
        super().__init__(message)


class DeadLetterQueue:
    """
    A queue for messages that failed processing and couldn't be retried.
    
    This implementation uses memory storage, but could be extended to use
    persistent storage.
    """
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
    
    def add_message(self, message_data: Dict[str, Any], error: MessageProcessingError):
        """
        Add a message to the dead letter queue.
        
        Args:
            message_data: The message data
            error: The error that caused the message to be dead-lettered
        """
        with self.lock:
            dead_letter = {
                "message": message_data,
                "error_message": str(error),
                "original_error": str(error.original_error),
                "timestamp": error.timestamp.isoformat(),
                "dlq_timestamp": datetime.now().isoformat()
            }
            self.messages.append(dead_letter)
            
            logger.warning(f"Added message to dead letter queue: {error}")
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Get all messages in the dead letter queue.
        
        Returns:
            A list of dead-lettered messages
        """
        with self.lock:
            return self.messages.copy()
    
    def clear(self):
        """Clear all messages from the dead letter queue."""
        with self.lock:
            self.messages.clear()
            logger.info("Cleared dead letter queue")


class RetryBackoffStrategy:
    """Strategy for calculating retry delay using exponential backoff."""
    
    def __init__(self, initial_delay: float = 1.0, max_delay: float = 60.0, backoff_factor: float = 2.0):
        """
        Initialize the retry backoff strategy.
        
        Args:
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Factor to multiply delay by after each retry
        """
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    def get_delay(self, retry_count: int) -> float:
        """
        Calculate the delay for a retry attempt.
        
        Args:
            retry_count: The number of previous retry attempts
            
        Returns:
            The delay in seconds
        """
        delay = self.initial_delay * (self.backoff_factor ** retry_count)
        return min(delay, self.max_delay)


class ErrorHandler:
    """
    Error handler for message queue operations.
    
    This class provides mechanisms for handling errors in message processing,
    including retry logic and dead letter queueing.
    """
    
    def __init__(self, max_retries: int = 3, retry_strategy: Optional[RetryBackoffStrategy] = None,
                 dead_letter_queue: Optional[DeadLetterQueue] = None):
        """
        Initialize the error handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_strategy: Strategy for calculating retry delays
            dead_letter_queue: Queue for messages that couldn't be processed
        """
        self.max_retries = max_retries
        self.retry_strategy = retry_strategy or RetryBackoffStrategy()
        self.dead_letter_queue = dead_letter_queue or DeadLetterQueue()
        self.retry_threads: Dict[str, threading.Thread] = {}
        self.retry_lock = threading.Lock()
        
        logger.info(f"Initialized ErrorHandler with max_retries={max_retries}")
    
    def handle_error(self, message_data: Dict[str, Any], error: Exception, 
                      retry_callback: Callable[[Dict[str, Any]], None], message_id: Optional[str] = None):
        """
        Handle an error in message processing.
        
        Args:
            message_data: The message data that caused the error
            error: The error that occurred
            retry_callback: Function to call to retry processing the message
            message_id: Optional ID for the message
        """
        # Generate a message ID if not provided
        if message_id is None:
            # Try to extract from message data or generate a new one
            message_id = str(message_data.get("id", hash(json.dumps(message_data, sort_keys=True))))
        
        # Determine if the error is retryable
        retryable = self._is_retryable_error(error)
        
        # Wrap the error
        processing_error = MessageProcessingError(
            message=f"Error processing message: {error}",
            message_data=message_data,
            error=error,
            retryable=retryable
        )
        
        if not retryable:
            logger.error(f"Non-retryable error for message {message_id}: {error}")
            self.dead_letter_queue.add_message(message_data, processing_error)
            return
        
        # Get retry count from message data or use 0 for first attempt
        retry_count = message_data.get("_retry_count", 0)
        
        if retry_count >= self.max_retries:
            logger.error(f"Max retries ({self.max_retries}) exceeded for message {message_id}")
            self.dead_letter_queue.add_message(message_data, processing_error)
            return
        
        # Increment retry count in message data
        message_data["_retry_count"] = retry_count + 1
        
        # Calculate delay for this retry
        delay = self.retry_strategy.get_delay(retry_count)
        
        logger.info(f"Scheduling retry {retry_count + 1}/{self.max_retries} for message {message_id} in {delay:.2f}s")
        
        # Schedule retry in a separate thread
        with self.retry_lock:
            # Cancel any existing retry for this message
            if message_id in self.retry_threads and self.retry_threads[message_id].is_alive():
                logger.info(f"Cancelling previous retry for message {message_id}")
                # We can't really cancel a thread, but we can remove it from our tracking
                del self.retry_threads[message_id]
            
            # Create new retry thread
            retry_thread = threading.Thread(
                target=self._execute_retry,
                args=(message_data, retry_callback, message_id, delay)
            )
            retry_thread.daemon = True
            self.retry_threads[message_id] = retry_thread
            retry_thread.start()
    
    def _execute_retry(self, message_data: Dict[str, Any], retry_callback: Callable[[Dict[str, Any]], None], 
                       message_id: str, delay: float):
        """
        Execute a retry after the specified delay.
        
        Args:
            message_data: The message data to retry
            retry_callback: Function to call with the message data
            message_id: ID of the message
            delay: Delay in seconds before retrying
        """
        try:
            # Sleep for the specified delay
            time.sleep(delay)
            
            logger.info(f"Executing retry for message {message_id}")
            
            # Call the retry callback
            retry_callback(message_data)
            
            logger.info(f"Retry for message {message_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error executing retry for message {message_id}: {e}")
            # This error is not handled further - it's a retry failure
        finally:
            # Remove thread from tracking
            with self.retry_lock:
                if message_id in self.retry_threads:
                    del self.retry_threads[message_id]
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error: The error to check
            
        Returns:
            True if the error is retryable, False otherwise
        """
        # Non-retryable errors
        non_retryable_errors = (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            json.JSONDecodeError
        )
        
        # Check if error is an instance of a non-retryable error type
        if isinstance(error, non_retryable_errors):
            return False
        
        # Network and transient errors are generally retryable
        retryable_error_names = (
            "ConnectionError",
            "Timeout",
            "ServerError",
            "CommunicationError",
            "TemporaryFailure"
        )
        
        # Check if error name contains any retryable error indicators
        error_name = type(error).__name__
        if any(indicator in error_name for indicator in retryable_error_names):
            return True
        
        # Default to retryable for unknown errors
        return True
    
    def get_dead_letter_messages(self) -> List[Dict[str, Any]]:
        """
        Get all messages in the dead letter queue.
        
        Returns:
            A list of dead-lettered messages
        """
        return self.dead_letter_queue.get_messages()
    
    def clear_dead_letter_queue(self):
        """Clear all messages from the dead letter queue."""
        self.dead_letter_queue.clear()
    
    def retry_dead_letter_message(self, index: int, retry_callback: Callable[[Dict[str, Any]], None]) -> bool:
        """
        Retry a specific message from the dead letter queue.
        
        Args:
            index: Index of the message in the dead letter queue
            retry_callback: Function to call with the message data
            
        Returns:
            True if message was successfully retried, False otherwise
        """
        messages = self.dead_letter_queue.get_messages()
        
        if 0 <= index < len(messages):
            message = messages[index]
            try:
                # Reset retry count
                message_data = message["message"]
                message_data["_retry_count"] = 0
                
                # Call retry callback directly
                retry_callback(message_data)
                
                # Remove from dead letter queue
                with self.dead_letter_queue.lock:
                    self.dead_letter_queue.messages.pop(index)
                
                logger.info(f"Successfully retried dead letter message at index {index}")
                return True
                
            except Exception as e:
                logger.error(f"Error retrying dead letter message at index {index}: {e}")
                return False
        else:
            logger.error(f"Invalid index {index} for dead letter queue of size {len(messages)}")
            return False


def create_error_handler(max_retries: int = 3, initial_delay: float = 1.0, 
                         max_delay: float = 60.0, backoff_factor: float = 2.0) -> ErrorHandler:
    """
    Factory function to create an ErrorHandler.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Factor to multiply delay by after each retry
        
    Returns:
        A configured ErrorHandler instance
    """
    retry_strategy = RetryBackoffStrategy(
        initial_delay=initial_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor
    )
    
    dead_letter_queue = DeadLetterQueue()
    
    return ErrorHandler(
        max_retries=max_retries,
        retry_strategy=retry_strategy,
        dead_letter_queue=dead_letter_queue
    ) 