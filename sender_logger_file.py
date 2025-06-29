#!/usr/bin/env python3
import socket
import struct
import time
import os
import sys

# Configuration
#SERVER_IP = "192.168.56.107"     # IP address of the receiver/server
SERVER_IP = "192.168.56.103" 
SERVER_PORT = 8888               # Listening port of the receiver
CHUNK_SIZE = 1024                # Size of each data chunk to send
#CHUNK_SIZE = 16 * 1024  # 即 16KB
INTERVAL = 0                     # Interval between sending chunks (in seconds)
N_ROUNDS = 3                     # Default number of rounds (can be overridden by command line)

# List of files to send (uncomment if needed)
FILE_LIST = [
#    "testfiles/64KB.file",
#    "testfiles/256KB.file",
#    "testfiles/8MB.file",
    "testfiles/64MB.file"
#    "testfiles/256MB.file",
#    "testfiles/512MB.file"
]

# Allow overriding N_ROUNDS via command-line argument
if len(sys.argv) >= 2:
    try:
        N_ROUNDS = int(sys.argv[1])
        print(f"[Config] Using N_ROUNDS = {N_ROUNDS} from argument")
    except ValueError:
        print("[Warning] Invalid round number argument. Using default.")

# Retry logic for establishing TCP connection
def connect_retry():
    for attempt in range(3):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_IP, SERVER_PORT))
            return s
        except Exception as e:
            print(f"[Retry] Connection failed (attempt {attempt + 1}): {e}")
            time.sleep(4)
    raise RuntimeError("Connection failed after maximum retries")

# Function to send file content in chunks, each with a timestamp prefix
def send_file(file_path, sock):
    with open(file_path, "rb") as f:
        chunk_num = 0
        while True:
            # Read payload (subtract 8 bytes for timestamp)
            payload = f.read(CHUNK_SIZE - 8)
            if not payload:
                break
            # Pack current time into 8 bytes (big-endian double)
            ts = struct.pack("!d", time.time())
            # Pad payload if smaller than CHUNK_SIZE - 8
            if len(payload) < CHUNK_SIZE - 8:
                payload += b'x' * (CHUNK_SIZE - 8 - len(payload))
            try:
                sock.sendall(ts + payload)
            except Exception as e:
                print(f"[Error] Send failed: {e}")
                return -1
            chunk_num += 1
            if INTERVAL > 0:
                time.sleep(INTERVAL)
    return chunk_num

# Optional: send number of rounds to receiver if SEND_ROUND_FLAG is set
if os.environ.get("SEND_ROUND_FLAG", "true").lower() == "true":
    first_conn = connect_retry()
    # Send N_ROUNDS as unsigned int (4 bytes)
    first_conn.sendall(struct.pack("!I", N_ROUNDS))
    first_conn.close()
    time.sleep(100)  # Wait before starting file transfer (for receiver preparation)

# Main loop: send each file N_ROUNDS times
for file_path in FILE_LIST:
    if not os.path.exists(file_path):
        print(f"[Error] File not found: {file_path}")
        continue

    for round_id in range(1, N_ROUNDS + 1):
        print(f"\n=== Sending file: {file_path}, Round {round_id} ===")
        sock = connect_retry()
        num_chunks = send_file(file_path, sock)
        sock.close()

        if num_chunks == -1:
            print(f"[Error] Failed to send file: {file_path} (Round {round_id})")
        else:
            print(f"[Client] Sent {num_chunks} chunks.")
        time.sleep(100)  # Sleep between rounds to ensure clean start
