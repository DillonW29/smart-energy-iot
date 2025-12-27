import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 5000))

print("Release 1 UDP Listener started...")

count = 0

while True:
    data, addr = sock.recvfrom(1024)
    count += 1
    print(f"[{count}] Received:", data.decode())
