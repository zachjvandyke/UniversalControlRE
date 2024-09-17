# ( ip.src == 192.168.0.167 || ip.dst == 192.168.0.167 ) && ((!tcp && data.len != 1061 && data.len != 79) || (tcp.payload && tcp.len != 12)) && !icmp

import select
import socket
import json
import errno
import struct

import colorama
colorama.init()


"""
--> Send Hello packet 


CONTROL OVER TCP
METER OVER UDP (52703)
"""


"""
Every three seconds
broadcast 255.255.255.255

53000 -> 47809

0000   ff ff ff ff ff ff 00 0a 92 00 6b c3 08 00 45 00   ..........k...E.
0010   00 6b 5a 4b 00 00 ff 11 9f e7 c0 a8 00 a7 ff ff   .kZK............
0020   ff ff cf 08 ba c1 00 57 d0 5f 55 43 00 01 08 cf   .......W._UC....
0030   44 41 65 00 00 00 00 04 00 80 48 1c 48 67 23 60   DAe.......H.Hg#`
0040   51 4f 92 4e 1e 46 91 50 51 d1 53 74 75 64 69 6f   QO.N.F.PQ.Studio
0050   4c 69 76 65 20 32 34 52 00 41 55 44 00 52 41 32   Live 24R.AUD.RA2
0060   45 32 32 32 32 32 32 32 32 00 53 74 75 64 69 6f   E22222222.Studio
0070   4c 69 76 65 20 32 34 52 00                        Live 24R.

# The first "StudioLive 24R" is used to check for the model and image on the display

# this is the packet sent to the UC Quantum HD connected via my iPhone @zach
51690 → 49162

0000   14 98 77 61 b1 66 8e f7 0f 33 b5 bb 08 00 45 00   ..wa.f...3....E.
0010   01 47 00 00 40 00 40 06 46 a7 0a 26 6f 76 0a 26   .G..@.@.F..&ov.&
0020   6f 48 c9 ea c0 0a 56 ee 7f 4c c5 2d cc a4 80 18   oH....V..L.-....
0030   08 0a 74 1b 00 00 01 01 08 0a 64 ea 6f 8b 17 19   ..t.......d.o...
0040   1f c7 55 43 00 01 08 00 55 4d 00 00 6a 00 70 fa   ..UC....UM..j.p.
0050   55 43 00 01 ff 00 4a 4d 68 00 6a 00 f5 00 00 00   UC....JMh.j.....
0060   7b 22 69 64 22 3a 20 22 53 75 62 73 63 72 69 62   {"id": "Subscrib
0070   65 22 2c 22 63 6c 69 65 6e 74 4e 61 6d 65 22 3a   e","clientName":
0080   20 22 55 6e 69 76 65 72 73 61 6c 20 43 6f 6e 74    "Universal Cont
0090   72 6f 6c 22 2c 22 63 6c 69 65 6e 74 49 6e 74 65   rol","clientInte
00a0   72 6e 61 6c 4e 61 6d 65 22 3a 20 22 75 63 72 65   rnalName": "ucre
00b0   6d 6f 74 65 61 70 70 22 2c 22 63 6c 69 65 6e 74   moteapp","client
00c0   54 79 70 65 22 3a 20 22 69 50 68 6f 6e 65 22 2c   Type": "iPhone",
00d0   22 63 6c 69 65 6e 74 44 65 73 63 72 69 70 74 69   "clientDescripti
00e0   6f 6e 22 3a 20 22 69 50 68 6f 6e 65 22 2c 22 63   on": "iPhone","c
00f0   6c 69 65 6e 74 49 64 65 6e 74 69 66 69 65 72 22   lientIdentifier"
0100   3a 20 22 42 45 37 30 35 42 35 42 2d 41 43 45 43   : "BE705B5B-ACEC
0110   2d 34 39 34 31 2d 39 41 42 41 2d 34 46 42 35 43   -4941-9ABA-4FB5C
0120   41 30 34 41 43 36 44 22 2c 22 63 6c 69 65 6e 74   A04AC6D","client
0130   4f 70 74 69 6f 6e 73 22 3a 20 22 22 2c 22 63 6c   Options": "","cl
0140   69 65 6e 74 45 6e 63 6f 64 69 6e 67 22 3a 20 32   ientEncoding": 2
0150   33 31 31 37 7d                                    3117}

"""


class Protocol:
    """
    # Protocol Spec
    # UC\x00\x01
    \x55\x43\x00\x01 + (short)(LittleEndian)packetLength + TWO_CHAR_CODE? + ?A? + \x00 + ?B? + \x00 + PAYLOAD

    """

    bytePrefix = b"\x55\x43\x00\x01"
    headerLength = len(bytePrefix) + 2

    A = b"\x68"  # These values might come from
    B = b"\x65"  # the broadcast discovery

    class __TwoWayMap(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            super().update(zip(kwargs.values(), kwargs.keys()))

        def __getattribute__(self, item):
            """
            # Use this one if you want to keep dict object methods
            if item in self: return self[item]
            return super().__getattribute__(item)
            """

            return self[item]

    MessagePrefix = __TwoWayMap(KeepAlive=b"KA",
                                Hello=b"UM",
                                JSON=b"JM",
                                Setting=b"PV",
                                Settings2=b"PL",
                                FileResource=b"FR",
                                FileResource2=b"FD",
                                UNKNOWN_REPLY=b"BO",
                                CompressedUnknown=b"CK",
                                )

# "global/identify" -> True/False

# TODO: Event loop in the API


class Client(Protocol):

    def __init__(self, host, port=53000):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # ['SOCK_DGRAM', 'SOCK_RAW', 'SOCK_RDM', 'SOCK_SEQPACKET', 'SOCK_STREAM']
        # 10.185.192.6
        conn.connect((host, port))
        conn.setblocking(0)
        self.conn = conn

        def craftSubscribe(overrides={}):
            data = dict(
                id="Subscribe",
                clientName="UC-Surface",
                clientInternalName="ucremoteapp",
                clientType="Android",
                clientDescription="zee3",
                clientIdentifier="133d066a929ea0ea",
                clientOptions="perm users levl redu rtan",
                clientEncoding=23106
            )
            data.update(overrides)

            # Desktop version:
            # {"id": "Subscribe","clientName": "Universal Control","clientInternalName": "ucapp","clientType": "PC","clientDescription": "FEATHERNET-PC","clientIdentifier": "FEATHERNET-PC","clientOptions": "perm users levl redu rtan","clientEncoding": 23106}

            return b"\xf2\x00\x00\x00" + json.dumps(data).encode()
        UDPport = 52703
        print(f"TCP {port}, UDP {UDPport}")
        self.send(self.MessagePrefix.Hello, struct.pack("<H", UDPport), customA=b"\x00")
        self.send(self.MessagePrefix.JSON, craftSubscribe(
            dict(clientDescription="Develop")))

        self.sendList("presets/channel")

        # self.listen()
    def listen(self):
        pass

    def send(self, byteCode: bytes, byteStream: bytes = b"", *, show: bool = True, customA=None, customB=None):
        A = customA or self.A
        B = customB or self.B

        # < : Little Endian
        # H : Unsigned Short
        payload = byteCode + (A + b"\x00" + B + b"\x00") + byteStream
        lengthBytes = struct.pack("<H", len(payload))

        data = self.bytePrefix + lengthBytes + payload

        if show:
            print("\033[31m" + "Sending payload, length: " +
                  str(len(data)) + "\033[0m")

        total_sent = 0
        while len(data):
            try:
                sent = self.conn.send(data)
                total_sent += sent
                data = data[sent:]
            except socket.error as e:
                if e.errno != errno.EAGAIN:
                    raise e
                select.select([], [self.conn], [])
        return 0

    def sendList(self, key: str):
        self.send(self.MessagePrefix.FileResource, b"\x01\x00" +
                  ("List"+key).encode() + b"\x00\x00")

    def sendProperty(self, key: str, state: bool):
        self.send(self.MessagePrefix.Setting, key.encode() +
                  b"\x00\x00\x00\x00\x00" + Client._onOffCode(bool))

    @staticmethod
    def _onOffCode(bool): return b"\x80\x3f" if bool else b"\x00\x00"

    def muteChannel(self, ch, bool: bool):
        "line/ch[1-32]/mute"
        "fxreturn/ch[1-4]/mute"
        "return/ch[1-3]/mute"  # Aux In
        assert 1 <= ch <= 32
        self.send(self.MessagePrefix.Setting,
                  f"line/ch{ch}/mute".encode() + b"\x00\x00\x00\x00\x00" + Client._onOffCode(bool))

    def _recv_raw(self, length: int):
        data = b""
        while len(data) != length:
            select.select([self.conn], [], [])
            data += self.conn.recv(length - len(data))
        return data

    def recv(self):
        buffer = b""

        buffer += self._recv_raw(self.headerLength)
        payload_size = struct.unpack("<H", buffer[-2:])[0]
        print(
            "\033[31m" + "Receiving payload of {} bytes...".format(payload_size) + "\033[0m")
        buffer += self._recv_raw(payload_size)

        if len(buffer) != self.headerLength + payload_size:
            raise Exception("RIP")

        # buffer += self.conn..recv(self.headerLength)
        # payload_size = struct.unpack("<H", buffer[-2:])[0]
        # print(
        #     "\033[31m" + "Receiving payload of {} bytes...".format(payload_size) + "\033[0m")
        # buffer += self.conn.recv(payload_size)

        return buffer


"""
0000   00 0a 92 00 6b c3 02 18 b9 e3 db e2 08 00 45 00   ....k.........E.
0010   00 4d e5 0b 40 00 80 06 00 00 c0 a8 00 e6 c0 a8   .M..@...........
0020   00 a7 c4 74 cf 08 e0 1a 59 c8 00 00 5f 98 50 18   ...t....Y..._.P.
0030   fa cc 83 1d 00 00 55 43 00 01 1f 00 4a 4d 68 00   ......UC....JMh.
0040   65 00 15 00 00 00 7b 22 69 64 22 3a 20 22 55 6e   e.....{"id": "Un
0050   73 75 62 73 63 72 69 62 65 22 7d                  subscribe"}

0000   00 00 0c c0 a8 00 00 09 2d 01 02 03 08 00 45 00   ........-.....E.
0010   00 4d 00 3e 00 00 40 06 f8 6b c0 a8 00 0a c0 a8   .M.>..@..k......
0020   00 a7 7f fb cf 08 00 00 02 bf 00 00 5d 92 50 18   ............].P.
0030   10 00 cc 8b 00 00 55 43 00 01 1f 00 4a 4d 68 00   ......UC....JMh.
0040   65 00 15 00 00 00 7b 22 69 64 22 3a 20 22 55 6e   e.....{"id": "Un
0050   73 75 62 73 63 72 69 62 65 22 7d                  subscribe"}

# unsubscribe = b"\x4a\x4d" + Protocol.A + b"\x00" + Protocol.B +         b"\x00\x15\x00\x00\x00\x7b\x22\x69\x64\x22\x3a\x20\x22\x55\x6e\x73\x75\x62\x73\x63\x72\x69\x62\x65\x22\x7d"
"""
# Turn on ..\x80\x3f
# Turn off ..\x80\x3f


"""
# MIX PERMISSIONS

# \x50\x56\x6e\x00\x65\x00\x70\x65\x72\x6d\x69\x73\x73\x69\x6f\x6e\x73\x2f\x6d\x69\x78\x5f\x70\x65\x72\x6d\x69\x73\x73\x69\x6f\x6e\x73\x00\x00\x00
# NAN # \x00\x00\x00\x00
# FOH # \x39\x8e\x63\x3d
# ALL # \x39\x8e\xe3\x3d
# 1   # \xab\xaa\x2a\x3e
# 2   # \x39\x8e\x63\x3e
# 3   # \xe4\x38\x8e\x3e
# 4   # \xab\xaa\xaa\x3e
# 5   # \x72\x1c\xc7\x3e
# 6   # \x39\x8e\xe3\x3e
# 7   # \x00\x00\x00\x3f
# 8   # \xe4\x38\x0e\x3f
# 9   # \xc7\x71\x1c\x3f
# 10  # \xab\xaa\x2a\x3f
# 11  # \x8e\xe3\x38\x3f
# 12  # \x72\x1c\x47\x3f
# 13  # \x55\x55\x55\x3f
# 14  # \x39\x8e\x63\x3f
# 15  # \x1c\xc7\x71\x3f
# 16  # \x00\x00\x80\x3f
"""


RESPONSE = {}


"""

0000   78 24 af 41 c7 d7 00 0a 92 00 6b c3 08 00 45 00   x$.A......k...E.
0010   00 4e 73 f4 00 00 ff 06 c4 b8 c0 a8 00 a7 c0 a8   .Ns.............
0020   01 05 cf 08 13 63 00 00 95 34 b0 d9 3d fe 50 18   .....c...4..=.P.
0030   57 14 3d 03 00 00 55 43 00 01 20 00 50 56 65 00   W.=...UC.. .PVe.
0040   68 00 6c 69 6e 65 2f 63 68 31 2f 64 63 61 2f 76   h.line/ch1/dca/v
0050   6f 6c 75 6d 65 00 00 00 ba c5 66 3f               olume.....f?


"\x78\x24\xaf\x41\xc7\xd7\x00\x0a\x92\x00\x6b\xc3\x08\x00\x45\x00" \
"\x00\x4e\x73\xf4\x00\x00\xff\x06\xc4\xb8\xc0\xa8\x00\xa7\xc0\xa8" \
"\x01\x05\xcf\x08\x13\x63\x00\x00\x95\x34\xb0\xd9\x3d\xfe\x50\x18" \
"\x57\x14\x3d\x03\x00\x00\x55\x43\x00\x01\x20\x00\x50\x56\x65\x00" \
"\x68\x00\x6c\x69\x6e\x65\x2f\x63\x68\x31\x2f\x64\x63\x61\x2f\x76" \
"\x6f\x6c\x75\x6d\x65\x00\x00\x00\xba\xc5\x66\x3f"


"""
