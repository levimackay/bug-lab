"""Wire format for the fleet event log.

Each record is a fixed 14-byte header followed by a variable-length UTF-8
payload:

    seq          uint32   record sequence number, starting at 0
    timestamp    float64  unix time the event was recorded
    payload_len  uint16   number of bytes in the payload that follows

The format is little-endian with no padding (`<`), so the header is exactly
``struct.calcsize(HEADER_FORMAT)`` bytes on every platform.
"""

import struct

HEADER_FORMAT = "<IdH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
