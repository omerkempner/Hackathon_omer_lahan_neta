import struct
import threading
import time
from select import select
from socket import *

import scapy.all as scapy
import queue
from getch import *


game_time = 10
magic_cookie = 0xabcddcba
# client_ip = scapy.get_if_addr("eth1")
client_ip = ''
print(client_ip)


def send_result(client_tcp_socket, time_out):
    # get_data_thread = threading.Thread(target=get_result, args=(data, time_out))
    # get_data_thread.start()
    # print("in send result")
    while time.time() < time_out:
        data  = getch()
        try:
            print(data)
            client_tcp_socket.send(data.encode('utf-8'))
            break
        except:  # ConnectionAbortedError | ConnectionResetError:
            break

# def get_result(data, time_out):
#     while time.time() < time_out:
#         data  = getch()



# function for getting message from server after the game starts
def get_from_server(client_tcp_socket):
    while True:
        try:
            data = client_tcp_socket.recv(1024)
            print(data.decode())
            if not data:
                break
        except:
            print("SERVER DISCONNECTED")
            break



def start():
        client_udp_socket = socket(AF_INET, SOCK_DGRAM)
        client_udp_socket.bind((client_ip, 13117))
        client_udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        client_udp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        client_udp_socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)

        print("insert client name")
        client_name = input()

        in_game = False
        print("Client started, listening for offer requests...")

        while not in_game:
            print("recv msg from server")
            try:
                data, serverAddress = client_udp_socket.recvfrom(7)
            except: 
                continue 
            print("after recv msg from server")
            (sent_cookie, msg_type, msg_server_port) = struct.unpack('!IbH', data)
            (ip, port) = serverAddress
            print("server ip: " + str(ip) + " server port: " + str(port) + " port2: " + str(msg_server_port) )

            if sent_cookie == magic_cookie and msg_type == 0x2:
                print("Received offer from: " + ip + " , attempting to connect... ")

                # accepting offer, sending team name
                client_tcp_socket = socket(AF_INET, SOCK_STREAM)
                try:
                    print("try to connec\n")
                    client_tcp_socket.connect((ip, msg_server_port))
                    print("send name\n")
                    client_tcp_socket.send(client_name.encode("utf-8"))
                except:
                    print("Server Disconnected")
                    break

                in_game = True
                print("in game!\n")
                client_udp_socket.close()

                try:
                    data = client_tcp_socket.recv(2048)
                    print("print what the client recived")
                    print(data.decode())
                except Exception:
                    print("server disconnected")
                    break

  # game starting
                time_out = time.time() + game_time

    
                send_data_thread = threading.Thread(target=send_result, args=(client_tcp_socket, time_out,))
                get_from_server_thread = threading.Thread(target=get_from_server, args=(client_tcp_socket,))
                
                send_data_thread.start()
                get_from_server_thread.start()
                
                send_data_thread.join()
                get_from_server_thread.join()
                

                #lahan neta 
                # send_data_thread = threading.Thread(target=send_result, args=(data, client_tcp_socket, time_out,))
                
                # get_from_server_thread = threading.Thread(target=get_from_server, args=(client_tcp_socket,))
                
                # send_data_thread.start()
                # get_from_server_thread.start()
                # send_data_thread.join()
                # get_from_server_thread.join()

                client_tcp_socket.close()

                print("Server disconnected, listening for offer requests...")

start()
