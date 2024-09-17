# packet.py
from dataclasses import dataclass
from typing import Optional, List, Union
import struct
import io


@dataclass
class AddressPair:
    a: int  # Corresponds to u16
    b: int  # Corresponds to u16


class UcPacket:
    pass


@dataclass
class JM(UcPacket):
    ap: AddressPair
    s: str


@dataclass
class UM(UcPacket):
    ap: AddressPair
    udp_port: int  # Corresponds to u16


@dataclass
class KA(UcPacket):
    ap: AddressPair


@dataclass
class PV(UcPacket):
    ap: AddressPair
    name: str
    val: float  # Corresponds to f32


@dataclass
class FR(UcPacket):
    ap: AddressPair
    some_number: int  # Corresponds to u16
    buf: str


@dataclass
class ZM(UcPacket):
    ap: AddressPair
    unknown: int  # Corresponds to u32
    compressed_payload: bytes


@dataclass
class PS(UcPacket):
    ap: AddressPair
    buf: bytes


@dataclass
class PL(UcPacket):
    ap: AddressPair
    name: str
    names: List[str]


def ser(packet: UcPacket) -> bytes:
    buf = io.BytesIO()
    write_packet(packet, buf)
    return buf.getvalue()


def write_address_pair(ap: AddressPair, w: io.BytesIO):
    w.write(struct.pack('<H', ap.a))
    w.write(struct.pack('<H', ap.b))


def write_packet(p: UcPacket, w: io.BytesIO):
    w.write(b'UC\x00\x01')

    if isinstance(p, JM):
        s = p.s
        ap = p.ap
        size = len(s) + 10  # 10 bytes for extra metadata
        w.write(struct.pack('<H', size))
        w.write(b'JM')
        write_address_pair(ap, w)
        w.write(struct.pack('<I', len(s)))
        w.write(s.encode('utf-8'))

    elif isinstance(p, UM):
        ap = p.ap
        udp_port = p.udp_port
        size = 8
        w.write(struct.pack('<H', size))
        w.write(b'UM')
        write_address_pair(ap, w)
        w.write(struct.pack('<H', udp_port))

    elif isinstance(p, KA):
        ap = p.ap
        size = 6
        w.write(struct.pack('<H', size))
        w.write(b'KA')
        write_address_pair(ap, w)

    elif isinstance(p, PV):
        ap = p.ap
        name = p.name
        val = p.val
        size = len(name) + 4  # Additional 4 bytes for the float value
        w.write(struct.pack('<H', size + 2 + 7))  # +2 for 'PV', +7 for padding
        w.write(b'PV')
        write_address_pair(ap, w)
        w.write(name.encode('utf-8'))
        w.write(b'\x00\x00\x00')  # Padding with 3 zeros
        w.write(struct.pack('<f', val))

    elif isinstance(p, FR):
        ap = p.ap
        some_number = p.some_number
        buf = p.buf
        size = len(buf) + 8
        w.write(struct.pack('<H', size))
        w.write(b'FR')
        write_address_pair(ap, w)
        w.write(struct.pack('<H', some_number))
        w.write(buf.encode('utf-8'))

    elif isinstance(p, ZM):
        ap = p.ap
        unknown = p.unknown
        compressed_payload = p.compressed_payload
        size = len(compressed_payload) + 6
        w.write(struct.pack('<H', size))
        w.write(b'ZM')
        write_address_pair(ap, w)
        w.write(struct.pack('<I', unknown))
        w.write(compressed_payload)

    elif isinstance(p, PS):
        ap = p.ap
        buf = p.buf
        size = len(buf) + 6
        w.write(struct.pack('<H', size))
        w.write(b'PS')
        write_address_pair(ap, w)
        w.write(buf)

    elif isinstance(p, PL):
        ap = p.ap
        name = p.name
        names = p.names
        size_of_names = sum(len(n) for n in names) + len(names)  # Names and newlines
        size = 6 + len(name) + 7 + size_of_names
        w.write(struct.pack('<H', size))
        w.write(b'PL')
        write_address_pair(ap, w)
        w.write(name.encode('utf-8'))
        w.write(b'\x00\x00\x00\x00\x00\x00\x00')  # Padding with 7 zeros
        for n in names:
            w.write(n.encode('utf-8'))
            w.write(b'\n')
    else:
        raise ValueError(f"Unknown UcPacket type: {type(p)}")


def parse_packet_contents(bytes_: bytes) -> UcPacket:
    if len(bytes_) < 6:
        raise ValueError("Packet contents too small")

    typ = bytes_[0:2]
    data = bytes_[2:]

    ap_a, ap_b = struct.unpack('<HH', data[0:4])
    address_pair = AddressPair(a=ap_a, b=ap_b)
    data = data[4:]  # Advance the data pointer

    if typ == b'JM':
        if len(data) < 4:
            raise ValueError("JM packet too short for length field")
        s_length = struct.unpack('<I', data[:4])[0]
        s = data[4:4 + s_length].decode('utf-8')
        return JM(ap=address_pair, s=s)

    elif typ == b'PV':
        if len(data) < 7:
            raise ValueError("PV packet too short")
        val = struct.unpack('<f', data[-4:])[0]
        name = data[:-7].decode('utf-8')  # Exclude padding and float
        return PV(ap=address_pair, name=name, val=val)

    elif typ == b'UM':
        if len(data) < 4:
            raise ValueError("UM packet too short")
        udp_port = struct.unpack('<H', data[2:4])[0]
        return UM(ap=address_pair, udp_port=udp_port)

    elif typ == b'KA':
        return KA(ap=address_pair)

    elif typ == b'ZM':
        unknown = struct.unpack('<I', data[0:4])[0]
        compressed_payload = data[4:]
        return ZM(ap=address_pair, unknown=unknown, compressed_payload=compressed_payload)

    elif typ == b'MS':
        # Ignore MS packets
        return None

    else:
        # Optionally ignore unknown packets
        return None


def read_udp_packet(stream: io.BytesIO) -> Optional[UcPacket]:
    header = stream.read(6)
    if len(header) < 6:
        raise ValueError("Packet too small to be valid")

    if header[0:2] != b'UC' or header[2:4] != b'\x00\x01':
        raise ValueError("Header magic bytes invalid")

    # Read the rest of the data as the packet content
    buf = stream.read()
    packet = parse_packet_contents(buf)
    return packet  # May return None for MS packets
