import os
import socket
import sys
import threading

client_socket = None
connected = False
CLIENT_STORAGE_DIR = "ClientStorage/"


def receive_messages():
    global connected
    while connected:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                print("\n[SERVER DISCONNECTED]")
                connected = False
                break

            # Fix CLI problem with multithreading
            sys.stdout.write("\033[2K\r")

            print(f"\n{message}")

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
                    print("/dir                         : Request directory list")
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
                    client_socket.send("disconnect".encode())
                    connected = False
                    client_socket.close()
                    print("Connection closed. Thank you!")
                case "/dir":
                    client_socket.send("dir".encode())
        except KeyboardInterrupt:
            if connected:
                client_socket.send("disconnect".encode())
                client_socket.close()
            print("\nExiting Client")
            sys.exit()


if __name__ == "__main__":
    start_client()
