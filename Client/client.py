from socket import *
import struct
import sys
import select

# ===== magic numbers ======
buf_size = 2<<10
udp_port = 13117
team_name = "Descendants of Turing"
magic_cookie = 0xabcddcba
offer_op_code = 0x2
timeout_interval = 10
timeout_waiting_for_game_start = 60

def acceptOffer():
    """
    Listens for offer broadcast from servers, returns a tuple (server_address,server_msg)
    """
    udp_sock = socket(AF_INET,SOCK_DGRAM)
    udp_sock.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    udp_sock.setsockopt(SOL_SOCKET,SO_BROADCAST,1)
    incoming_msg, server_ip_address = udp_sock.recvfrom(buf_size)
    msg_tuple = struct.unpack('IbH',incoming_msg) #I = unsigned int, 4 bytes magic cookie, b = byte of offer msg, H = unsigned short, 2 bytes representing server port
    if msg_tuple[0] != magic_cookie or msg_tuple[1] != offer_op_code:
        return False
    udp_sock.close()
    return (server_ip_address[0],msg_tuple[2]) #returning server's ip and server's tcp port  

def handleTCP(server_ip,server_port):
    """
    Creates a tcp connection with the server and returns the tcp socket for the game
    """
    tcp_sock = socket(AF_INET, SOCK_STREAM)
    try:
        tcp_sock.connect((server_ip,server_port))
        tcp_sock.send((team_name + "\n").encode())
    except:
        tcp_sock.close()
        return False
    return tcp_sock

def gameMode(tcp_sock):
    """
    This function simulates the game via the tcp connection with the server
    """
    tcp_sock.settimeout(timeout_waiting_for_game_start)
    try:
        welcome_msg = tcp_sock.recv(buf_size).decode()
        print(welcome_msg)
    except:
        tcp_sock.close()
        return

    server_has_answered = False
    tcp_sock.settimeout(timeout_interval)
    reads,_,_ = select.select([sys.stdin,tcp_sock],[],[],timeout_interval)
    if sys.stdin in reads:
        ans = sys.stdin.readline()[0]
        try:
            tcp_sock.send(ans.encode())
        except:
            tcp_sock.close()
            return
    if tcp_sock in reads:
        print(tcp_sock.recv(buf_size).decode())
        server_has_answered = True
    if not server_has_answered:
        try:
            print(tcp_sock.recv(buf_size).decode())
        except:
            pass
    tcp_sock.close()
    



is_first_cycle = True
while 1:
    if is_first_cycle == True:
        print("Client started, listening for offer requests...")
    else:
        print("Server disconnected, listening for offer requests...")
    server_offer = acceptOffer()
    if server_offer != False:
        print("Received offer from " + server_offer[0] + ", attempting to connect...")
        tcp_sock = handleTCP(server_offer[0],server_offer[1])
        if tcp_sock!=False:
            gameMode(tcp_sock)
            is_first_cycle = False