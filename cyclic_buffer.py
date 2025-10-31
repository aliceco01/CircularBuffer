"""
Circular buffer implementation for Message objects with FIFO behavior.
"""
from typing import Optional
from message import Message


class BufferOverflowError(Exception):
    """Exception raised when pushing to a full buffer without overwrite enabled."""
    pass


class BufferUnderflowError(Exception):
    """Exception raised when popping from an empty buffer."""
    pass


class CyclicBuffer:
    """
    Fixed-capacity circular buffer implementing FIFO behavior for Message objects.
    
    Features:
    - Configurable overwrite behavior
    - Overflow and underflow protection with flag management
    - Dynamic capacity resizing
    - O(1) push/pop operations
    """
    
    def __init__(self, capacity: int, overwrite: bool = False):
        """
        Initialize circular buffer.
        
        Args:
            capacity: Maximum number of messages (1-100)
            overwrite: If True, overwrite oldest message when full
            
        Raises:
            ValueError: If capacity < 1 or capacity > 100
        """
        if not (1 <= capacity <= 100):
            raise ValueError(f"Capacity must be between 1 and 100, got {capacity}")
        
        self._capacity = capacity
        self._overwrite = overwrite
        self._buffer = [None] * capacity
        self._head = 0  # Position to write next element
        self._tail = 0  # Position to read next element
        self._size = 0  # Current number of elements
        
        # Status flags
        self._overflow_flag = False
        self._underflow_flag = False
        self._data_loss_resize_flag = False
    
    def push(self, message: Message) -> bool:
        """
        Add message to buffer (FIFO).
        
        Args:
            message: Message object to add
            
        Returns:
            True if successful, False if buffer full and overwrite disabled
            
        Raises:
            BufferOverflowError: If buffer is full and overwrite is False
        """
        if self.is_full():
            if not self._overwrite:
                self._overflow_flag = True
                print(f"Buffer overflow: Cannot push to full buffer (capacity={self._capacity})")
                raise BufferOverflowError("Buffer is full and overwrite is disabled")
            else:
                # Overwrite mode: remove oldest message
                self._overflow_flag = True
                print(f"Buffer overflow: Overwriting oldest message")
                # Move tail forward to discard oldest
                self._tail = (self._tail + 1) % self._capacity
                self._size -= 1
        
        # Add message at head position
        self._buffer[self._head] = message
        self._head = (self._head + 1) % self._capacity
        self._size += 1
        
        return True
    
    def pop(self) -> Optional[Message]:
        """
        Remove and return oldest message from buffer (FIFO).
        
        Returns:
            Oldest Message object, or None if buffer is empty
            
        Raises:
            BufferUnderflowError: If buffer is empty
        """
        if self.is_empty():
            self._underflow_flag = True
            print(f"Buffer underflow: Cannot pop from empty buffer")
            raise BufferUnderflowError("Buffer is empty")
        
        # Get message from tail position
        message = self._buffer[self._tail]
        self._buffer[self._tail] = None  # Clear reference
        self._tail = (self._tail + 1) % self._capacity
        self._size -= 1
        
        return message
    
    def resize(self, new_capacity: int) -> bool:
        """
        Change buffer capacity at runtime.
        
        Args:
            new_capacity: New maximum capacity (1-100)
            
        Returns:
            True if resize successful, False if rejected
            
        Raises:
            ValueError: If new_capacity < 1 or > 100
        """
        if not (1 <= new_capacity <= 100):
            raise ValueError(f"Capacity must be between 1 and 100, got {new_capacity}")
        
        # Case 1: Increasing capacity - always allowed
        if new_capacity > self._capacity:
            self._expand_buffer(new_capacity)
            return True
        
        # Case 2: Decreasing capacity
        if new_capacity < self._capacity:
            # Check if current size fits in new capacity
            if self._size <= new_capacity:
                # No data loss - shrink buffer
                self._shrink_buffer(new_capacity)
                return True
            else:
                # Current size exceeds new capacity
                if self._overwrite:
                    # Discard oldest messages
                    self._shrink_with_data_loss(new_capacity)
                    self._data_loss_resize_flag = True
                    print(f"Resize with data loss: Discarded {self._size - new_capacity} messages")
                    return True
                else:
                    # Reject resize
                    print(f"Resize rejected: Would lose {self._size - new_capacity} messages (overwrite=False)")
                    return False
        
        # Case 3: Same capacity - no-op
        return True
    
    def _expand_buffer(self, new_capacity: int):
        """Expand buffer capacity while preserving order."""
        new_buffer = [None] * new_capacity
        
        # Copy existing messages in order
        for i in range(self._size):
            old_index = (self._tail + i) % self._capacity
            new_buffer[i] = self._buffer[old_index]
        
        self._buffer = new_buffer
        self._tail = 0
        self._head = self._size
        self._capacity = new_capacity
    
    def _shrink_buffer(self, new_capacity: int):
        """Shrink buffer capacity without data loss."""
        new_buffer = [None] * new_capacity
        
        # Copy all existing messages
        for i in range(self._size):
            old_index = (self._tail + i) % self._capacity
            new_buffer[i] = self._buffer[old_index]
        
        self._buffer = new_buffer
        self._tail = 0
        self._head = self._size
        self._capacity = new_capacity
    
    def _shrink_with_data_loss(self, new_capacity: int):
        """Shrink buffer capacity, discarding oldest messages."""
        new_buffer = [None] * new_capacity
        
        # Calculate how many messages to keep (newest ones)
        messages_to_discard = self._size - new_capacity
        
        # Copy only the newest messages
        for i in range(new_capacity):
            old_index = (self._tail + messages_to_discard + i) % self._capacity
            new_buffer[i] = self._buffer[old_index]
        
        self._buffer = new_buffer
        self._tail = 0
        self._head = new_capacity
        self._size = new_capacity
        self._capacity = new_capacity
    
    def get_size(self) -> int:
        """Return current number of messages in buffer."""
        return self._size
    
    def get_max_size(self) -> int:
        """Return current maximum capacity of buffer."""
        return self._capacity
    
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return self._size == 0
    
    def is_full(self) -> bool:
        """Check if buffer is full."""
        return self._size == self._capacity
    
    def clear_flags(self):
        """Clear all status flags."""
        self._overflow_flag = False
        self._underflow_flag = False
        self._data_loss_resize_flag = False
    
    def get_overflow_flag(self) -> bool:
        """
        Get and clear overflow flag (sticky flag behavior).
        
        Returns:
            True if overflow occurred since last check
        """
        flag = self._overflow_flag
        self._overflow_flag = False
        return flag
    
    def get_underflow_flag(self) -> bool:
        """
        Get and clear underflow flag (sticky flag behavior).
        
        Returns:
            True if underflow occurred since last check
        """
        flag = self._underflow_flag
        self._underflow_flag = False
        return flag
    
    def get_data_loss_resize_flag(self) -> bool:
        """
        Get and clear data loss resize flag (sticky flag behavior).
        
        Returns:
            True if data was lost during resize since last check
        """
        flag = self._data_loss_resize_flag
        self._data_loss_resize_flag = False
        return flag
    
    def __str__(self):
        """String representation of buffer state."""
        return (f"CyclicBuffer(size={self._size}/{self._capacity}, "
                f"overwrite={self._overwrite})")
    
    def __len__(self):
        """Return current size (enables len(buffer))."""
        return self._size
