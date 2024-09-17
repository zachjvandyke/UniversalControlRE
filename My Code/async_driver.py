# async_driver.py
import asyncio
import io
import struct
import json
import zlib
from typing import Optional
from packet import UcPacket, AddressPair, JM, UM, KA, ZM, read_udp_packet
from async_packet import PacketCodec


class AsyncUcDriver:
    def __init__(self, reader, writer, udp_port):
        self.reader = reader
        self.writer = writer
        self.cmd_queue = asyncio.Queue()
        self.udp_port = udp_port
        self.tasks = []
        self.udp_transport = None
        self.udp_protocol = None
        self.codec = PacketCodec()

    @classmethod
    async def create(cls, ip_address):
        reader, writer = await asyncio.open_connection(ip_address, 49162)
        self = cls(reader, writer, udp_port=0)

        # Set up UDP socket
        loop = asyncio.get_event_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: UdpProtocol(),
            local_addr=('0.0.0.0', 0)
        )
        udp_port = transport.get_extra_info('sockname')[1]
        self.udp_port = udp_port
        self.udp_transport = transport
        self.udp_protocol = protocol

        # Start tasks
        self.tasks.append(asyncio.create_task(self.heartbeat_task()))
        self.tasks.append(asyncio.create_task(self.sender_task()))
        return self

    async def heartbeat_task(self):
        try:
            while True:
                await asyncio.sleep(2)
                await self.send(KA(ap=AddressPair(a=0x68, b=0x6a)))
        except asyncio.CancelledError:
            pass

    async def sender_task(self):
        try:
            while True:
                packet = await self.cmd_queue.get()
                data = self.codec.encode(packet)
                self.writer.write(data)
                await self.writer.drain()
                print_packet(packet, outgoing=True)
        except asyncio.CancelledError:
            pass

    async def send(self, packet: UcPacket):
        await self.cmd_queue.put(packet)

    async def um(self, port_number: int):
        await self.send(UM(
            ap=AddressPair(a=0, b=0x66),
            udp_port=port_number
        ))

    async def subscribe(self):
        print(f"Subscribing on UDP port {self.udp_port}")
        await self.um(self.udp_port)
        sub_msg_uc = {
            "id": "Subscribe",
            "clientName": "Universal Control",
            "clientInternalName": "ucremoteapp",
            "clientType": "iPhone",
            "clientDescription": "iPhone",
            "clientIdentifier": "BE705B5B-ACEC-4941-9ABA-4FB5CA04AC6D",
            "clientOptions": "",
            "clientEncoding": 23117
        }
        await self.send(JM(
            ap=AddressPair(a=0x68, b=0x6a),
            s=json.dumps(sub_msg_uc)
        ))

    async def read_responses(self):
        try:
            while True:
                packet = await self.codec.decode(self.reader)
                if packet is None:
                    print("Connection closed by the server.")
                    break  # Connection closed
                print_packet(packet, outgoing=False)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error reading response: {e}")

    async def close(self):
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close the writer
        self.writer.close()
        await self.writer.wait_closed()

        # Close UDP transport if needed
        if self.udp_transport:
            self.udp_transport.close()


def print_packet(packet: UcPacket, outgoing: bool):
    direction = "->" if outgoing else "<-"
    if isinstance(packet, ZM):
        try:
            decoded_data = decode_zm_packet_data(packet.compressed_payload)
            print(f"{direction} ZM ({packet.ap}, {packet.unknown}, {decoded_data})")
        except Exception as e:
            print(f"{direction} ZM ({packet.ap}, {packet.unknown}, <Error decompressing ZM packet data: {e}>)")
    elif isinstance(packet, UM):
        print(f"{direction} UM ({packet.ap}, {packet.udp_port})")
    else:
        print(f"{direction} {packet}")


def decode_zm_packet_data(data: bytes) -> str:
    """
    Decompresses the compressed_payload from a ZM packet using raw DEFLATE.
    Skips the first two bytes and decompresses the rest.
    """
    try:
        compressed_data = data[2:]
        # Create a decompressor object for raw DEFLATE data
        decompressor = zlib.decompressobj(wbits=-15)
        # Decompress with a max_length limit
        payload = decompressor.decompress(compressed_data, max_length=600000)
        # Decode the decompressed payload as a UTF-8 string
        return payload.decode('utf-8')
    except Exception as e:
        # Raise an error if decompression fails
        raise ValueError(f"Failed to decompress ZM packet data: {e}")


class UdpProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport
        print("UDP connection established")

    def datagram_received(self, data, addr):
        if len(data) != 159:
            print(f"Received {len(data)} bytes from {addr}")
        try:
            stream = io.BytesIO(data)
            packet: Optional[UcPacket] = read_udp_packet(stream)
            if packet is not None:
                print_packet(packet, outgoing=False)
            else:
                # MS packet received; skip printing
                pass
        except Exception as e:
            print(f"Failed to parse UDP packet: {e}")

    def error_received(self, exc):
        print(f"Error received on UDP: {exc}")

    def connection_lost(self, exc):
        print("UDP connection closed")
