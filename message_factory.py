#Factory function/class to parse string and create appropriate message object

"""
Factory for creating Message objects from string input.
"""
from message import Message, TelemetryMessage, LocationMessage, SettingsMessage


class InvalidMessageError(Exception):
    """Exception raised for unrecognized or malformed messages."""
    pass


class MessageFactory:
    """Factory class for creating appropriate Message objects from strings."""
    
    MESSAGE_TYPES = {
        "GPS": LocationMessage,
        "TEL": TelemetryMessage,
        "SET": SettingsMessage
    }
    
    @staticmethod
    def create_message(msg_string: str) -> Message:
        """
        Parse a message string and create appropriate Message object.
        
        Message format: sssmmmddd...
        - sss: 3-char sensor ID (000-999)
        - mmm: 3-char message type (GPS/TEL/SET)
        - ddd...: variable-length data payload
        
        Args:
            msg_string: Fixed-format message string
            
        Returns:
            Appropriate Message subclass instance
            
        Raises:
            InvalidMessageError: If message format is invalid
        """
        # Validate minimum length
        if len(msg_string) < 6:
            raise InvalidMessageError(
                f"Message too short. Expected at least 6 characters, got {len(msg_string)}"
            )
        
        # Extract sensor ID (first 3 characters)
        sensor_id_str = msg_string[0:3]
        try:
            sensor_id = int(sensor_id_str)
            if not (0 <= sensor_id <= 999):
                raise ValueError()
        except ValueError:
            raise InvalidMessageError(
                f"Invalid sensor ID format: '{sensor_id_str}'. Must be 3-digit number (000-999)"
            )
        
        # Extract message type (characters 3-5, 0-indexed)
        msg_type = msg_string[3:6]
        
        # Validate message type
        if msg_type not in MessageFactory.MESSAGE_TYPES:
            raise InvalidMessageError(
                f"Unknown message type: '{msg_type}'. Must be one of: GPS, TEL, SET"
            )
        
        # Extract data payload (everything after position 6)
        data = msg_string[6:]
        
        # Create appropriate message object
        message_class = MessageFactory.MESSAGE_TYPES[msg_type]
        message = message_class(sensor_id)
        
        # Parse data payload
        try:
            message.parse_data(data)
        except ValueError as e:
            raise InvalidMessageError(f"Failed to parse {msg_type} message data: {e}")
        
        return message


def create_message_from_string(msg_string: str) -> Message:
    """
    Convenience function for creating messages.
    
    Args:
        msg_string: Fixed-format message string
        
    Returns:
        Appropriate Message subclass instance
    """
    return MessageFactory.create_message(msg_string)
