
# Circular Buffer with Message Classification

A **production-grade cyclic buffer** implementing **FIFO semantics** for fixed-format sensor messages with **automatic type classification**, **dynamic resizing**, and **robust error handling**.

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

## Edge Cases Handled

- [x] Push to full buffer (with/without overwrite)
- [x] Pop from empty buffer
- [x] Invalid sensor ID (`"ABC"`, `1000`)
- [x] Malformed GPS (`+91.0`, `+180.000001`, missing sign)
- [x] Resize during full/partial fill
- [x] Resize rejection when `overwrite=False`
- [x] Data loss tracking on shrink
- [x] GPS edge values: `±180.000000`, `±90.000000`
- [x] Zero-capacity prevention
- [x] Max capacity = 100 (memory safety)

---

## Test Suite (`test_circular_buffer.py`)

| # | Test Case |
|---|-----------|
| 1 | FIFO ordering preserved |
| 2 | Overflow → exception + `overflow_flag` |
| 3 | Overwrite mode replaces oldest |
| 4 | Underflow → exception + `underflow_flag` |
| 5 | Resize expand → no data loss |
| 6 | Resize shrink → no loss when size ≤ new_capacity |
| 7 | Resize shrink + overwrite → discards oldest + sets `data_loss_resize` |
| 8 | Resize reject when `overwrite=False` and data would be lost |
| 9 | Invalid message → skipped with warning |
| 10 | GPS coordinate edge cases |
| 11 | `clear_flags()` resets all sticky flags |

Run with:
```bash
python3 -m venv venv && source venv/bin/activate
pip install pytest
pytest test_circular_buffer.py -v