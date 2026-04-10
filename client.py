import os
import socket
import sys
import threading

client_socket = None
connected = False
CLIENT_STORAGE_DIR = "ClientStorage/"


store_ack_event = threading.Event()


def receive_messages():
    global connected
    while connected:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                print("\n[SERVER DISCONNECTED]")
                connected = False
                break

            msgSplit = message.split(" ")
            command = msgSplit[0]

            #            print(f"\n{message}")

            match command:
                case "msg":
                    rcvMsg = ""
                    for i in range(1, len(msgSplit)):
                        rcvMsg = rcvMsg + " " + msgSplit[i]

                    print("\n" + rcvMsg)
                case "dir":
                    print("\n--- Server Directory ---")
                    for i in range(1, len(msgSplit)):
                        print(msgSplit[i])
                case "store_ack":
                    store_ack_event.set()
                case "get_incoming":
                    filename = msgSplit[1]
                    filesize = int(msgSplit[2])

                    client_socket.send("get_ack".encode())

                    filepath = os.path.join(CLIENT_STORAGE_DIR, filename)
                    with open(filepath, "wb") as f:
                        bytes_received = 0
                        while bytes_received < filesize:
                            chunk = client_socket.recv(
                                min(4096, filesize - bytes_received)
                            )
                            if not chunk:
                                break
                            f.write(chunk)
                            bytes_received += len(chunk)

                    print(f"\nFile received from Server: {filename}")

            # Fix CLI problem with multithreading
            sys.stdout.write("\033[2K\r")

            sys.stdout.write(">> ")
            sys.stdout.flush()
        except Exception as e:
            if connected:
                sys.stdout.write("\033[2K\r")
                print(f"\n[Error] Connection lost: {e}")
            connected = False
            break


def start_client():
    global client_socket, connected

    if not os.path.exists(CLIENT_STORAGE_DIR):
        os.mkdir("ClientStorage")
    while True:
        try:
            user_input = input(">> ").strip()
            if not user_input:
                continue

            input_split = user_input.split(" ")
            command = input_split[0].lower()

            match command:
                case "/?":
                    print("\n--- Command Help ---")
                    print("/join <server_ip_add> <port> : Connect to server")
                    print("/leave                       : Disconnect from server")
                    print("/register <handle>           : Register alias")
                    print("/store <filename>            : Send file to server")
                    print(
                        "/dir                         : Request directory list of Server"
                    )
                    print(
                        "/cdir                         : Get Directory List of Client"
                    )
                    print("/get <filename>              : Fetch file from server")
                    print("--------------------\n")
                    continue
                case "/join":
                    if connected:
                        print("Error: Already connected to server")
                        continue
                    if len(input_split) != 3:
                        print("Error: Syntax is join <server_ip_add> <port")
                        continue

                    ip, port = input_split[1], int(input_split[2])

                    try:
                        client_socket = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM
                        )
                        client_socket.connect((ip, port))
                        connected = True

                        receive_thread = threading.Thread(target=receive_messages)
                        receive_thread.daemon = True
                        receive_thread.start()
                    except Exception as e:
                        print(f"Error connecting to server: {e}")
                case "/leave":
                    if not connected:
                        print("Error: Not Connected")
                        continue
                    client_socket.send("disconnect".encode())
                    connected = False
                    client_socket.close()
                    print("Connection closed. Thank you!")
                case "/dir":
                    if not connected:
                        print("Error: Not Connected")
                        continue
                    client_socket.send("dir".encode())
                case "/register":
                    if len(input_split) != 2:
                        print("Error: Syntax is /register <handle>")
                    if not connected:
                        print("Error: Not Connected")
                        continue
                    else:
                        client_socket.send(f"handle {input_split[1]}".encode())
                case "/store":
                    if not connected:
                        print("Error: Not Connected")
                        continue
                    if len(input_split) != 2:
                        print("Error: Syntax is /store <filename>")
                        continue

                    filename = input_split[1]
                    filepath = os.path.join(CLIENT_STORAGE_DIR, filename)
                    if not os.path.exists(filepath):
                        print(
                            f"Error: File '{filename}' not in Client Storage Directory"
                        )
                        continue

                    filesize = os.path.getsize(filepath)
                    store_ack_event.clear()

                    client_socket.send(f"store {filename} {filesize}".encode())

                    if store_ack_event.wait(timeout=5):
                        with open(filepath, "rb") as f:
                            client_socket.sendall(f.read())
                    else:
                        print("Error: Server timed out. Could not upload file ")
                case "/cdir":
                    print("--- Client Directory ---")
                    for dir in os.listdir(CLIENT_STORAGE_DIR):
                        print(dir)
                case "/get":
                    if not connected:
                        print("Error: Not Connected")
                        continue
                    if len(input_split) != 2:
                        print("Error: Syntax is /get <filename>")
                        continue

                    filename = input_split[1]
                    client_socket.send(f"get {filename}".encode())
                case _:
                    print("Error: Invalid Command")

        except KeyboardInterrupt:
            if connected:
                client_socket.send("disconnect".encode())
                client_socket.close()
            print("\nExiting Client")
            sys.exit()


if __name__ == "__main__":
    start_client()
