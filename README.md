
# Circular Buffer with Message Classification

A production-grade cyclic buffer, implementing FIFO semantics for fixed-format sensor messages with automatic type classification**, dynamic resizing, and error handling.

Supports three message types:
- `GPS`: Location (longitude, latitude)
- `TEL`: Telemetry (battery %)
- `SET`: Settings (on/off, rate)


## Design 

| Feature | Implementation |
|--------|----------------|
| **OOP** | `Message` ABC with three concrete subclasses |
| **Parsing** | Factory pattern (`create_message`) for clean separation |
| **Buffer** | Index-based ring buffer with `head`/`tail` pointers → O(1) ops |
| **Resize** | Full buffer reconstruction preserves FIFO order |
| **Flags** | Sticky state; cleared only via `clear_flags()` |
| **Errors** | Custom exceptions + console feedback |

---

## Edge Cases 

- Push to full buffer (with/without overwrite)
- Pop from empty buffer
- Invalid sensor ID
- Malformed GPS 
- Resize during full/partial fill
- Resize rejection when `overwrite=False`
- Data loss tracking on shrink
- GPS edge values: `±180.000000`, `±90.000000`
- Zero-capacity prevention
- Max capacity = 100

---

## Test Suite

| # | Test Case |
|---|-----------|
| 1 | FIFO ordering 
| 2 | Overflow - `overflow_flag` 
| 3 | Overwrite mode replaces oldest |
| 4 | Underflow  `underflow_flag` exception |
| 5 | Resize expand  |
| 6 | Resize shrink  when size ≤ new_capacity |
| 7 | Resize shrink -  overwrite  discards oldest + sets `data_loss_resize` |
| 8 | Resize reject when `overwrite=False` and data would be lost |
| 9 | Invalid message → skipped with warning |
| 10 | GPS coordinate edge cases |
| 11 | `clear_flags()` resets all sticky flags |

Run with:
```bash
python3 -m venv venv && source venv/bin/activate
pip install pytest
pytest test_circular_buffer.py -v