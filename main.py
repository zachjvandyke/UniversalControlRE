import zlib

hexnum = "554300011f00505668006a00676c6f62616c2f6d6978657242797061737300000000003f"

print(bytearray.fromhex(hexnum).decode('ascii'))

