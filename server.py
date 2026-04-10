import datetime
import os
import socket
import sys
import threading

HOST = sys.argv[1]
PORT = int(sys.argv[2])
SERVER_STORAGE_DIR = "ServerStorage/"

connected_clients = {}


def handle_client(conn, addr):
    print(f"[NEW Connection] {addr} connected.")

    conn.send("connect success".encode())

    connected_clients[conn] = {"handle": None}

    connected = True
    while connected:
        try:
            message = conn.recv(1024).decode().strip()
            if not message:
                break

            mSplit = message.split(" ")
            command = mSplit[0]
            args = mSplit[1] if len(mSplit) > 1 else ""

            match command:
                case "disconnect":
                    conn.send("disconnect success".encode())
                    connected = False
                case "dir":
                    dirCombined = ""
                    for dir in os.listdir(SERVER_STORAGE_DIR):
                        dirCombined = dirCombined + " " + dir

                    conn.send(f"dir {dirCombined}".encode())
                case "handle":
                    handle = args
                    connected_clients[conn]["handle"] = handle
                    conn.send(f"Welcome {handle}!".encode())
        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
            break

    if conn in connected_clients:
        del connected_clients[conn]

    conn.close()
    print(f"f[DISCONNECTED] {addr} disconnected")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    while True:
        # Wait for Clients
        conn, addr = server.accept()

        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


if __name__ == "__main__":
    start_server()
