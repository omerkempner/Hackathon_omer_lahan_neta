import struct
import random
import time
from socket import *
# from _thread import *
import threading

import scapy.all as scapy

l = threading.Lock()

BrightBlack = u"\u001b[30;1m"
BrightRed = u"\u001b[31;1m"
BrightGreen_ANSI = u"\u001b[32;1m"
BrightYellow = u"\u001b[33;1m"
BrightBlue_ANSI = u"\u001b[34;1m"
BrightMagenta = u"\u001b[35;1m"
BrightCyan = u"\u001b[36;1m"
BrightWhite = u"\u001b[37;1m"
Black = u"\u001b[30m"
BackgroundBrightWhite_ANSI = u"\u001b[47;1m"
BackgroundGreen_ANSI = u"\u001b[42m"
BackgroundBrightRed = u"\u001b[41;1m"
Reset = u"\u001b[0m"
Bold = u"\u001b[1m"

accepting_time = 30
game_time = 20
reloading_time = 20

global_timer = 10
threaded_client_list = {}

client1_name = ""
client2_name = ""

client1_conn = 0 
client2_conn = 0 

result = 0

continue_game = True
first_ans = -1 
ans = -1 

server_ip = scapy.get_if_addr("eth1")
# server_ip = '127.0.0.1'
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind((server_ip, 0))
serverSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)  # enable broadcasts
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)

server_tcp_socket = socket(AF_INET, SOCK_STREAM)
server_tcp_socket.bind((server_ip, 0))
server_tcp_socket.listen(1)

broadcast_address = '172.1.255.255'
broadcast_port = 13117

magic_cookie = 0xabcddcba
message_type = 0x2
server_tcp_port = server_tcp_socket.getsockname()[1]

def create_random_equation():
    operator_list = ["+", "-"]
    equation_numbers = random.randint(2, 3)
    eq = str(random.randint(1, 20))
    number= int(eq)
    sum = number
    for i in range(1, equation_numbers):
        oper_index = random.randint(0, 1)
        eq += operator_list[oper_index]
        temp = str(random.randint(1, 10))
        number= int(temp)
        if (oper_index  == 0):
            sum= sum +number
        else:
            sum= sum -number
        eq += temp

    meesage_q = "How much is "
    meesage_q += eq
    meesage_q += "?\n\n"
    
    global result
    result = sum

    return meesage_q



# function that manages the game with the client
def thread_for_game(connection, client_name):
    global continue_game, ans, first_ans
    while time.time() < global_timer and continue_game:
            try:
                connection.settimeout(max(global_timer - time.time(), 0))
                data = connection.recv(2048)
                if data:
                    l.acquire()
                    continue_game = False 
                    first_ans = client_name 
                    ans = data.decode('utf-8')
                    l.relese()       
                    break
                   #compare data to the correct ans
            except Exception:
                continue
   

# function for getting the team name from the client
def threaded_client(connection, client_num, timer_for_connections,index):
    got_team_name = False
    try:
        connection.settimeout(max(timer_for_connections - time.time(), 0))
        data = connection.recv(2048)
        got_team_name = True
    except Exception:
        return

    if got_team_name:
        thread_team_name = data.decode('utf-8')

        l.acquire()
        if client_num == 1:
            global client1_conn, client1_name
            client1_name = thread_team_name
            client1_conn = connection
        else:
            global client2_conn, client2_name
            client2_name = thread_team_name
            client2_conn = connection
        l.release()
    else:
        threaded_client_list.pop(index)
        connection.close()

def accept_connections():
    #run until 2 clients connect
    #wait 10 secondes for each connection
    timer_for_connections = time.time() + accepting_time
    client1 = False
    client2 = False

    while not client1 or not client2:
        try:
            server_tcp_socket.settimeout(max(timer_for_connections - time.time(), 0))
            conn, address = server_tcp_socket.accept()
        except Exception:
            break

        if not client1:
            client_num = 1
            client1 = True
        elif not client2:
            client_num = 2
            client2 = True
        else:
            break

        #create thread for each client and start it 
        t = threading.Thread(target=threaded_client,args=(conn, client_num, timer_for_connections,client_num,))
        
        threaded_client_list[client_num] = t
        t.start()


def start_game():
    #teams_dictionary = {}
    client1 = {}
    client2 = {}
    
    print(BrightBlack + BackgroundBrightWhite_ANSI + "  Server started, listening on IP address:" + server_ip + Reset)

    invite_message = struct.pack('!IbH', magic_cookie, message_type, server_tcp_port) #IbH - big endian\little endian.. format

    #thread for connections 
    t = threading.Thread(target=accept_connections, args=())
    t.start()

    for i in range(10):
        serverSocket.sendto(invite_message, (broadcast_address, broadcast_port))
        time.sleep(1)

    t.join()

    if len(threaded_client_list) == 0 or client1_conn == 0 or client2_conn == 0:
        print(BrightBlue_ANSI + "No one has connected, or No one sent team name :(" + Reset + "\n")
        return

    # welcome message
    welcome_message = BrightBlack + BackgroundBrightWhite_ANSI + Bold
    welcome_message += "$Welcome to Quick Maths$" + Reset + "\n"
    welcome_message += BrightGreen_ANSI + BackgroundGreen_ANSI + "Player 1:  " 
    welcome_message += client1_name + Reset 
    welcome_message += "\n" + BackgroundBrightRed
    welcome_message += BrightWhite + "Player 2:  " 
    welcome_message += client2_name
    welcome_message += Reset
    welcome_message += "\n"
    welcome_message += "==\n"
    welcome_message += "Please answer the following question as fast as you can:\n\n"


    message_q = create_random_equation()

    welcome_message += message_q

    client1_conn.send(welcome_message.encode('utf-8'))
    client2_conn.send(welcome_message.encode('utf-8'))


    print(BrightRed + " ************************************" + Reset)

    # game starts
    l.acquire()
    global global_timer
    global_timer = time.time() + game_time
    l.release()

    client1_threadGame = threading.Thread(target=thread_for_game, args=(client1_conn, client1_name))
    client2_threadGame = threading.Thread(target=thread_for_game, args=(client2_conn, client2_name))
    
    client1_threadGame.start()
    client2_threadGame.start()
    
    end_message =  """
           _____       ___       ___  ___   _____  
          /  ___|     /   |     /   |/   | |  ___| 
          | |        / /| |    / /|   /| | | |__   
          | |  _    / ___ |   / / |__/ | | |  __|  
          | |_| |  / /  | |  / /       | | | |___  
          \_____/ /_/   |_| /_/        |_| |_____|
           _____   _     _   _____   _____   
          /  _  \ | |   / / |  ___| |  _  \  
          | | | | | |  / /  | |__   | |_| |  
          | | | | | | / /   |  __|  |  _  /  
          | |_| | | |/ /    | |___  | | \ \  
          \_____/ |___/     |_____| |_|  \_\
          \n"""

    end_message += "The correct answer was " + str(result) + "!\n"
    


    if first_ans == -1: 
       end_message += "DRAW :( \n" 
    elif ans == result: 
        end_message += "Congratulations to the winner: " + first_ans 
    else: 
        if first_ans == client1_name: 
            end_message += "Congratulations to the winner: " + client2_name 
        else: 
            end_message += "Congratulations to the winner: " + client1_name
    

    try:
        client1_conn.send(end_message.encode('utf-8'))
        client2_conn.send(end_message.encode('utf-8'))
    except Exception:
        print("exception")
 
    # time.sleep(game_time)

    print(end_message)

    client1_conn.close()
    client2_conn.close()

    print("Server Reloading")
    time.sleep(reloading_time)


while True:
    start_game()
