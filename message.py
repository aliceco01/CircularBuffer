## Abstract Message base class and the three message classes implementations


"""
Abstract Message base class and concrete message type implementations.
"""
from abc import ABC, abstractmethod


class Message(ABC):
    """Abstract base class for all message types."""
    
    def __init__(self, sensor_id: int, msg_type: str):
        """
        Initialize base message.
        
        Args:
            sensor_id: Sensor ID (0-999)
            msg_type: Message type string
        """
        if not (0 <= sensor_id <= 999):
            raise ValueError(f"Sensor ID must be between 0 and 999, got {sensor_id}")
        
        self.sensor_id = sensor_id
        self.msg_type = msg_type
    
    @abstractmethod
    def parse_data(self, data: str):
        """Parse message-specific data payload."""
        pass
    
    def __str__(self):
        """String representation of the message."""
        return f"{self.__class__.__name__}(sensor_id={self.sensor_id})"


class TelemetryMessage(Message):
    """Telemetry message containing battery status."""
    
    def __init__(self, sensor_id: int):
        super().__init__(sensor_id, "TEL")
        self.battery_status = None
    
    def parse_data(self, data: str):
        """
        Parse battery status from data.
        
        Args:
            data: String containing battery percentage
        """
        try:
            self.battery_status = int(data)
            if not (0 <= self.battery_status <= 100):
                raise ValueError(f"Battery status must be between 0 and 100, got {self.battery_status}")
        except ValueError as e:
            raise ValueError(f"Invalid telemetry data format: {e}")
    
    def __str__(self):
        return f"TelemetryMessage(sensor_id={self.sensor_id}, battery={self.battery_status}%)"


class LocationMessage(Message):
    """Location message containing GPS coordinates."""
    
    def __init__(self, sensor_id: int):
        super().__init__(sensor_id, "GPS")
        self.longitude = None
        self.latitude = None
    
    def parse_data(self, data: str):
        """
        Parse longitude and latitude from data.
        
        Args:
            data: String containing "longitude,latitude"
        """
        try:
            parts = data.split(',')
            if len(parts) != 2:
                raise ValueError("GPS data must contain exactly 2 comma-separated values")
            
            self.longitude = float(parts[0])
            self.latitude = float(parts[1])
            
            # Validate ranges
            if not (-180 <= self.longitude <= 180):
                raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")
            if not (-90 <= self.latitude <= 90):
                raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid GPS data format: {e}")
    
    def __str__(self):
        return f"LocationMessage(sensor_id={self.sensor_id}, lon={self.longitude}, lat={self.latitude})"


class SettingsMessage(Message):
    """Settings message containing on/off state and message rate."""
    
    def __init__(self, sensor_id: int):
        super().__init__(sensor_id, "SET")
        self.on_off = None
        self.msgs_per_second = None
    
    def parse_data(self, data: str):
        """
        Parse settings from data.
        
        Args:
            data: String containing "on_off,msgs_per_second"
        """
        try:
            parts = data.split(',')
            if len(parts) != 2:
                raise ValueError("Settings data must contain exactly 2 comma-separated values")
            
            on_off_val = int(parts[0])
            if on_off_val not in (0, 1):
                raise ValueError(f"on_off must be 0 or 1, got {on_off_val}")
            self.on_off = bool(on_off_val)
            
            self.msgs_per_second = int(parts[1])
            if not (0 <= self.msgs_per_second <= 1000):
                raise ValueError(f"msgs_per_second must be between 0 and 1000, got {self.msgs_per_second}")
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid settings data format: {e}")
    
    def __str__(self):
        return f"SettingsMessage(sensor_id={self.sensor_id}, on={self.on_off}, rate={self.msgs_per_second})"
    

    