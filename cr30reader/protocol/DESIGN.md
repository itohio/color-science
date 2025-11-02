# Protocol Package Design

## Overview

The `protocol` package handles low-level communication with the CR30 colorimeter device. It provides asynchronous serial communication, packet building/parsing, and device protocol management.

## Package Structure

```
protocol/
├── __init__.py        # Package exports
├── device.py          # CR30Device - Raw serial communication
├── protocol.py         # CR30Protocol - Device-specific commands
├── packets.py         # CR30Packet, PacketBuilder, PacketParser - Packet handling
└── DESIGN.md          # This document
```

## Dependencies

**External Dependencies:**
- `asyncio` - Asynchronous programming
- `serial_asyncio` - Asynchronous serial communication
- `struct` - Binary data packing/unpacking
- `typing` - Type hints

**Internal Dependencies:**
- None (lowest level package)

## Core Classes

### CR30Device
**Purpose**: Raw byte-level serial communication with CR30 device

**Key Responsibilities:**
- Establish serial connection
- Handle asynchronous frame reception
- Manage device state and information
- Provide raw packet send/receive operations
- Creates and uses `PacketBuilder` instance for packet construction
- Creates and uses `PacketParser` instance for packet validation and payload extraction

**Interface:**
```python
class CR30Device:
    def __init__(self, port: str, baudrate: int, verbose: bool = True)
    async def connect() -> None
    async def disconnect() -> None
    async def send_raw(packet: bytes) -> None
    async def recv(timeout: Optional[float] = None) -> Optional[bytes]
    async def send_recv(start: int, cmd: int, subcmd: int = 0, 
                       param: int = 0, data: Optional[bytes] = None, 
                       timeout: float = 1.0) -> Optional[bytes]
    def build_packet(start: int, cmd: int, subcmd: int = 0,
                     param: int = 0, data: Optional[bytes] = None) -> bytes
    def _extract_payload_bytes(packet: bytes) -> bytes
    
    # Properties
    @property
    def name(self) -> str
    @property
    def model(self) -> str
    @property
    def serial_number(self) -> str
    @property
    def fw_version(self) -> str
```

### CR30Protocol
**Purpose**: High-level device protocol commands and measurement operations

**Key Responsibilities:**
- Device handshake and initialization
- Calibration procedures
- Measurement orchestration
- SPD data reconstruction

**Interface:**
```python
class CR30Protocol(CR30Device):
    async def handshake() -> None
    async def calibrate() -> None
    async def trigger_measurement() -> bytes
    async def read_measurement(timeout_per_step: float = 1.5) -> Dict[str, Any]
```

### CR30Packet
**Purpose**: Represents a CR30 protocol packet (60 bytes). Acts as a dataclass-like structure with properties that reference specific bytes.

**Key Features:**
- Properties for start, cmd, subcmd, param, payload that reference specific byte positions
- Automatic checksum calculation
- Validation of packet structure
- Conversion to bytes and hex strings

**Interface:**
```python
class CR30Packet:
    PACKET_SIZE = 60
    PAYLOAD_SIZE = 52
    
    def __init__(data: Optional[bytes] = None)
    
    @property
    def start(self) -> int
    @property
    def cmd(self) -> int
    @property
    def subcmd(self) -> int
    @property
    def param(self) -> int
    @property
    def payload(self) -> bytes
    
    def calculate_checksum() -> int
    def verify_checksum() -> bool
    def is_valid() -> bool
    def to_bytes() -> bytes
    def to_hex(separator: str = ' ') -> str
    
    @classmethod
    def from_bytes(data: bytes) -> CR30Packet
```

### PacketBuilder
**Purpose**: Build CR30 protocol packets using CR30Packet

**Interface:**
```python
class PacketBuilder:
    def build_packet(start: int, cmd: int, subcmd: int = 0, 
                     param: int = 0, data: Optional[bytes] = None) -> bytes
    def build_handshake_packet(cmd: int, subcmd: int = 0, 
                              param: int = 0, data: Optional[bytes] = None) -> bytes
    def build_command_packet(cmd: int, subcmd: int = 0, 
                               param: int = 0, data: Optional[bytes] = None) -> bytes
```

### PacketParser
**Purpose**: Parse received CR30 protocol packets using CR30Packet. Maintains state for multi-packet operations (e.g., SPD reconstruction from multiple chunks).

**Key Features:**
- Stateful: Accumulates SPD data from multiple chunk packets
- Handles chunk types 0x10, 0x11, 0x12, 0x13 internally
- Tracks received chunks to prevent duplicates
- Returns chunk information as packets are processed

**Interface:**
```python
class PacketParser:
    def __init__()
    def is_valid_packet(packet: bytes) -> bool
    def extract_payload(packet: bytes) -> bytes
    def parse_header(packet: bytes) -> CR30Packet
    def parse_device_info(packet: bytes) -> Dict[str, str]
    def parse_measurement_header(packet: bytes) -> CR30Packet
    def parse_spd_chunk(packet: bytes) -> Dict[str, Any]
    def reset_spd_collection() -> None
    def get_accumulated_spd() -> bytes
    def get_chunks_info() -> List[Dict[str, Any]]
    def is_spd_complete() -> bool
    def verify_checksum(packet: bytes) -> bool
    def parse_packet(packet: bytes) -> CR30Packet
```

## Design Patterns

### Asynchronous Communication
- Uses `asyncio.Queue` for frame buffering
- Non-blocking serial I/O with `serial_asyncio`
- Callback system for real-time packet processing

### Packet Structure
- 60-byte fixed-length packets
- Header: start(1) + cmd(1) + subcmd(1) + param(1)
- Payload: 52 bytes of data
- Footer: marker(1) + checksum(1)

### Error Handling
- Timeout-based error detection
- Packet structure validation via `PacketParser.is_valid_packet()`
- Graceful connection management
- Invalid packets are dropped silently in receive loop

### Packet Building/Parsing
- `CR30Packet` is the core dataclass-like structure representing a 60-byte packet
- `PacketBuilder` and `PacketParser` use `CR30Packet` internally
- `CR30Device` creates instances of `PacketBuilder` and `PacketParser` in `__init__()`
- `CR30Device` delegates packet building to its `PacketBuilder` instance
- `CR30Device` delegates packet validation to its `PacketParser` instance
- `CR30Device` delegates payload extraction to its `PacketParser` instance
- This ensures Single Responsibility: device handles communication, packet classes handle packet structure
- `PacketParser` is designed to support stateful operations (e.g., accumulating SPD data from multiple packets)

## Open Questions

1. **Connection Resilience**: How should the protocol handle connection drops and automatic reconnection?
   1. Ideally device should not disconnect. We fail if it does.

2. **Packet Validation**: Should we implement more sophisticated packet validation beyond checksums?
   1. Not yet.

3. **Flow Control**: How should we handle backpressure when the device sends data faster than we can process?
   1. Should not be an issue. it is a slow device.

4. **Protocol Versioning**: How should we handle different firmware versions that might have protocol changes?
   1. When we encounter different firmware  versions we will implement them in a separate class.

5. **Debugging Support**: What logging and debugging features should be built into the protocol layer?
   1. Verbose logging of bytes sent/received.

6. **Performance Monitoring**: Should we track communication performance metrics (packets/sec, latency)?
   1. No

7. **Configuration**: How should serial port parameters be configured and validated?
   1. Pass to serial connection function

8. **Error Recovery**: What strategies should be used when packets are corrupted or lost?
   1. Fail gracefully

9.  **Concurrent Access**: How should multiple threads/processes access the same device?
    1.  They should not

10. **Protocol Extensions**: How should we design for future protocol enhancements?
    1.  Factory pattern should cover different protocol implementations.
    2.  If we discover differences we would determine what implementation to use after handshake.

