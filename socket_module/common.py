# remote/net/common.py
import struct, json

def send_with_len(sock, data: bytes):
    sock.sendall(struct.pack("!I", len(data)) + data)

def recv_with_len(sock):
    size_data = sock.recv(4)
    if not size_data:
        return None
    size = struct.unpack("!I", size_data)[0]
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def send_json(sock, obj):
    send_with_len(sock, json.dumps(obj).encode())

def recv_json(sock):
    data = recv_with_len(sock)
    if not data:
        return {}
    return json.loads(data.decode())
