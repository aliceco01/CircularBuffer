"""
Comprehensive test suite for Circular Buffer implementation.
"""
import pytest
from cyclic_buffer import CyclicBuffer, BufferOverflowError, BufferUnderflowError
from message_factory import MessageFactory, InvalidMessageError
from message import TelemetryMessage, LocationMessage, SettingsMessage


class TestMessageParsing:
    """Test message parsing and validation."""
    
    def test_valid_telemetry_message(self):
        msg = MessageFactory.create_message("042TEL85")
        assert isinstance(msg, TelemetryMessage)
        assert msg.sensor_id == 42
        assert msg.battery_status == 85
    
    def test_valid_gps_message(self):
        msg = MessageFactory.create_message("001GPS-73.994454,40.750042")
        assert isinstance(msg, LocationMessage)
        assert msg.sensor_id == 1
        assert msg.longitude == -73.994454
        assert msg.latitude == 40.750042
    
    def test_valid_settings_message(self):
        msg = MessageFactory.create_message("123SET1,10")
        assert isinstance(msg, SettingsMessage)
        assert msg.sensor_id == 123
        assert msg.on_off is True
        assert msg.msgs_per_second == 10
    
    def test_invalid_sensor_id_format(self):
        with pytest.raises(InvalidMessageError):
            MessageFactory.create_message("ABCGPS1.0,2.0")
    
    def test_invalid_sensor_id_range(self):
        # 999 is valid (max value)
        msg = MessageFactory.create_message("999GPS1.0,2.0")
        assert msg.sensor_id == 999
        
        # Sensor IDs can't exceed 999 due to 3-char format
        # Test would require 4+ chars which fails at parsing stage
    
    def test_invalid_message_type(self):
        with pytest.raises(InvalidMessageError):
            MessageFactory.create_message("001XYZ123")
    
    def test_message_too_short(self):
        with pytest.raises(InvalidMessageError):
            MessageFactory.create_message("001GP")
    
    def test_telemetry_invalid_battery_range(self):
        with pytest.raises(InvalidMessageError):
            MessageFactory.create_message("001TEL101")
        with pytest.raises(InvalidMessageError):
            MessageFactory.create_message("001TEL-1")
    
    def test_gps_invalid_coordinate_range(self):
        with pytest.raises(InvalidMessageError):
            MessageFactory.create_message("001GPS-200.0,40.0")  # Invalid longitude
        with pytest.raises(InvalidMessageError):
            MessageFactory.create_message("001GPS-73.0,100.0")  # Invalid latitude
    
    def test_settings_invalid_on_off(self):
        with pytest.raises(InvalidMessageError):
            MessageFactory.create_message("001SET2,10")  # on_off must be 0 or 1
    
    def test_settings_invalid_rate_range(self):
        with pytest.raises(InvalidMessageError):
            MessageFactory.create_message("001SET1,1001")


class TestBasicBufferOperations:
    """Test basic buffer push/pop operations."""
    
    def test_buffer_initialization(self):
        buffer = CyclicBuffer(capacity=5)
        assert buffer.get_size() == 0
        assert buffer.get_max_size() == 5
        assert buffer.is_empty()
        assert not buffer.is_full()
    
    def test_push_and_pop_single_message(self):
        buffer = CyclicBuffer(capacity=3)
        msg = MessageFactory.create_message("001TEL50")
        
        buffer.push(msg)
        assert buffer.get_size() == 1
        assert not buffer.is_empty()
        
        popped = buffer.pop()
        assert popped.sensor_id == 1
        assert buffer.get_size() == 0
        assert buffer.is_empty()
    
    def test_fifo_ordering(self):
        buffer = CyclicBuffer(capacity=5)
        
        # Push multiple messages
        msg1 = MessageFactory.create_message("001TEL10")
        msg2 = MessageFactory.create_message("002TEL20")
        msg3 = MessageFactory.create_message("003TEL30")
        
        buffer.push(msg1)
        buffer.push(msg2)
        buffer.push(msg3)
        
        # Pop in FIFO order
        assert buffer.pop().sensor_id == 1
        assert buffer.pop().sensor_id == 2
        assert buffer.pop().sensor_id == 3
    
    def test_mixed_message_types(self):
        buffer = CyclicBuffer(capacity=5)
        
        buffer.push(MessageFactory.create_message("001GPS-73.0,40.0"))
        buffer.push(MessageFactory.create_message("002TEL75"))
        buffer.push(MessageFactory.create_message("003SET1,100"))
        
        msg1 = buffer.pop()
        msg2 = buffer.pop()
        msg3 = buffer.pop()
        
        assert isinstance(msg1, LocationMessage)
        assert isinstance(msg2, TelemetryMessage)
        assert isinstance(msg3, SettingsMessage)


class TestBufferOverflow:
    """Test buffer overflow conditions."""
    
    def test_overflow_without_overwrite_raises_exception(self):
        buffer = CyclicBuffer(capacity=2, overwrite=False)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        
        assert buffer.is_full()
        
        with pytest.raises(BufferOverflowError):
            buffer.push(MessageFactory.create_message("003TEL30"))
    
    def test_overflow_flag_set_on_overflow(self):
        buffer = CyclicBuffer(capacity=2, overwrite=False)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        
        try:
            buffer.push(MessageFactory.create_message("003TEL30"))
        except BufferOverflowError:
            pass
        
        assert buffer.get_overflow_flag() is True
        # Flag should be cleared after reading
        assert buffer.get_overflow_flag() is False
    
    def test_overflow_with_overwrite_replaces_oldest(self):
        buffer = CyclicBuffer(capacity=2, overwrite=True)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        buffer.push(MessageFactory.create_message("003TEL30"))  # Should overwrite first
        
        assert buffer.get_size() == 2
        
        # First message should be gone, second and third remain
        msg1 = buffer.pop()
        assert msg1.sensor_id == 2
        msg2 = buffer.pop()
        assert msg2.sensor_id == 3


class TestBufferUnderflow:
    """Test buffer underflow conditions."""
    
    def test_underflow_raises_exception(self):
        buffer = CyclicBuffer(capacity=3)
        
        with pytest.raises(BufferUnderflowError):
            buffer.pop()
    
    def test_underflow_flag_set(self):
        buffer = CyclicBuffer(capacity=3)
        
        try:
            buffer.pop()
        except BufferUnderflowError:
            pass
        
        assert buffer.get_underflow_flag() is True
        assert buffer.get_underflow_flag() is False  # Cleared after reading
    
    def test_underflow_after_emptying_buffer(self):
        buffer = CyclicBuffer(capacity=3)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.pop()
        
        with pytest.raises(BufferUnderflowError):
            buffer.pop()


class TestBufferResize:
    """Test dynamic buffer resizing."""
    
    def test_resize_increase_capacity(self):
        buffer = CyclicBuffer(capacity=3)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        
        assert buffer.resize(5) is True
        assert buffer.get_max_size() == 5
        assert buffer.get_size() == 2
        
        # Original messages should be preserved
        assert buffer.pop().sensor_id == 1
        assert buffer.pop().sensor_id == 2
    
    def test_resize_decrease_no_data_loss(self):
        buffer = CyclicBuffer(capacity=5)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        
        assert buffer.resize(3) is True
        assert buffer.get_max_size() == 3
        assert buffer.get_size() == 2
        
        # Messages preserved
        assert buffer.pop().sensor_id == 1
        assert buffer.pop().sensor_id == 2
    
    def test_resize_decrease_with_data_loss_overwrite_true(self):
        buffer = CyclicBuffer(capacity=5, overwrite=True)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        buffer.push(MessageFactory.create_message("003TEL30"))
        buffer.push(MessageFactory.create_message("004TEL40"))
        
        assert buffer.resize(2) is True
        assert buffer.get_max_size() == 2
        assert buffer.get_size() == 2
        
        # Oldest messages discarded, newest kept
        assert buffer.pop().sensor_id == 3
        assert buffer.pop().sensor_id == 4
        
        assert buffer.get_data_loss_resize_flag() is True
    
    def test_resize_decrease_rejected_overwrite_false(self):
        buffer = CyclicBuffer(capacity=5, overwrite=False)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        buffer.push(MessageFactory.create_message("003TEL30"))
        
        # Should reject resize
        assert buffer.resize(2) is False
        assert buffer.get_max_size() == 5  # Capacity unchanged
        assert buffer.get_size() == 3  # Data unchanged
    
    def test_resize_invalid_capacity(self):
        buffer = CyclicBuffer(capacity=5)
        
        with pytest.raises(ValueError):
            buffer.resize(0)
        
        with pytest.raises(ValueError):
            buffer.resize(101)
    
    def test_resize_preserves_fifo_order(self):
        buffer = CyclicBuffer(capacity=3)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        buffer.push(MessageFactory.create_message("003TEL30"))
        
        buffer.resize(5)
        
        # Order should be preserved
        assert buffer.pop().sensor_id == 1
        assert buffer.pop().sensor_id == 2
        assert buffer.pop().sensor_id == 3


class TestCircularBehavior:
    """Test circular wrapping behavior."""
    
    def test_circular_wrap_around(self):
        buffer = CyclicBuffer(capacity=3)
        
        # Fill buffer
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        buffer.push(MessageFactory.create_message("003TEL30"))
        
        # Pop one
        buffer.pop()
        
        # Push another (should wrap)
        buffer.push(MessageFactory.create_message("004TEL40"))
        
        assert buffer.get_size() == 3
        
        # Check FIFO order
        assert buffer.pop().sensor_id == 2
        assert buffer.pop().sensor_id == 3
        assert buffer.pop().sensor_id == 4
    
    def test_multiple_wrap_cycles(self):
        buffer = CyclicBuffer(capacity=2, overwrite=True)
        
        for i in range(10):
            buffer.push(MessageFactory.create_message(f"{i:03d}TEL{i*10}"))
            if i >= 2:  # Start popping after buffer has 2 items
                buffer.pop()
        
        assert buffer.get_size() == 2


class TestFlagManagement:
    """Test flag clearing and sticky behavior."""
    
    def test_clear_flags_clears_all(self):
        buffer = CyclicBuffer(capacity=2, overwrite=True)
        
        # Trigger overflow
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        buffer.push(MessageFactory.create_message("003TEL30"))
        
        # Trigger underflow
        buffer.pop()
        buffer.pop()
        try:
            buffer.pop()
        except BufferUnderflowError:
            pass
        
        # Trigger data loss resize
        buffer.push(MessageFactory.create_message("004TEL40"))
        buffer.push(MessageFactory.create_message("005TEL50"))
        buffer.resize(1)
        
        buffer.clear_flags()
        
        assert buffer.get_overflow_flag() is False
        assert buffer.get_underflow_flag() is False
        assert buffer.get_data_loss_resize_flag() is False
    
    def test_flags_sticky_until_read(self):
        buffer = CyclicBuffer(capacity=2, overwrite=False)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        
        # Trigger overflow
        try:
            buffer.push(MessageFactory.create_message("003TEL30"))
        except BufferOverflowError:
            pass
        
        # Multiple operations shouldn't clear flag
        buffer.pop()
        buffer.push(MessageFactory.create_message("004TEL40"))
        
        # Flag should still be set
        assert buffer.get_overflow_flag() is True
        # Now cleared
        assert buffer.get_overflow_flag() is False


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_capacity_one_buffer(self):
        buffer = CyclicBuffer(capacity=1)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        assert buffer.is_full()
        
        msg = buffer.pop()
        assert msg.sensor_id == 1
        assert buffer.is_empty()
    
    def test_capacity_one_with_overwrite(self):
        buffer = CyclicBuffer(capacity=1, overwrite=True)
        
        buffer.push(MessageFactory.create_message("001TEL10"))
        buffer.push(MessageFactory.create_message("002TEL20"))
        
        msg = buffer.pop()
        assert msg.sensor_id == 2  # First was overwritten
    
    def test_sensor_id_edge_cases(self):
        # Test boundary sensor IDs
        msg1 = MessageFactory.create_message("000TEL10")
        assert msg1.sensor_id == 0
        
        msg2 = MessageFactory.create_message("999TEL20")
        assert msg2.sensor_id == 999
    
    def test_gps_coordinate_boundaries(self):
        msg1 = MessageFactory.create_message("001GPS-180.0,-90.0")
        assert msg1.longitude == -180.0
        assert msg1.latitude == -90.0
        
        msg2 = MessageFactory.create_message("001GPS180.0,90.0")
        assert msg2.longitude == 180.0
        assert msg2.latitude == 90.0
    
    def test_settings_rate_boundaries(self):
        msg1 = MessageFactory.create_message("001SET0,0")
        assert msg1.on_off is False
        assert msg1.msgs_per_second == 0
        
        msg2 = MessageFactory.create_message("001SET1,1000")
        assert msg2.on_off is True
        assert msg2.msgs_per_second == 1000
    
    def test_empty_data_payload(self):
        # Should fail - data required
        with pytest.raises(InvalidMessageError):
            MessageFactory.create_message("001TEL")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])