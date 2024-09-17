# async_packet.py
import struct
from typing import Optional, Union
import asyncio
from packet import UcPacket, parse_packet_contents, ser


class PacketCodec:
    def __init__(self):
        self.buffer = bytearray()

    async def decode(self, reader: asyncio.StreamReader) -> Optional[UcPacket]:
        while True:
            if len(self.buffer) < 6:
                # Read enough bytes for the header
                data = await reader.read(6 - len(self.buffer))
                if not data:
                    return None  # Connection closed
                self.buffer.extend(data)

            if len(self.buffer) >= 6:
                header = self.buffer[:6]
                if header[0:2] != b'UC' or header[2:4] != b'\x00\x01':
                    raise ValueError("Header magic bytes invalid")

                size = struct.unpack('<H', header[4:6])[0]
                total_length = 6 + size

                while len(self.buffer) < total_length:
                    # Read the remaining bytes
                    data = await reader.read(total_length - len(self.buffer))
                    if not data:
                        return None  # Connection closed
                    self.buffer.extend(data)

                packet_data = self.buffer[6:total_length]
                packet = parse_packet_contents(packet_data)
                # Remove the processed packet from the buffer
                self.buffer = self.buffer[total_length:]
                return packet
            else:
                # Need more data
                data = await reader.read(1024)
                if not data:
                    return None  # Connection closed
                self.buffer.extend(data)

    def encode(self, packet: UcPacket) -> bytes:
        return ser(packet)
