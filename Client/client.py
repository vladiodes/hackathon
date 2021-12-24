from socket import *
import struct
import sys
import threading
import select

# ===== magic numbers ======
buf_size = 2<<10
udp_port = 13117
team_name = "Nice name"
magic_cookie = 0xabcddcba
offer_op_code = 0x2

def acceptOffer():
    """
    Listens for offer broadcast from servers, returns a tuple (server_address,server_msg)
    """
    udp_sock = socket(AF_INET,SOCK_DGRAM)
    udp_sock.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    udp_sock.setsockopt(SOL_SOCKET,SO_BROADCAST,1)
    udp_sock.bind(('',udp_port))
    incoming_msg, server_ip_address = udp_sock.recvfrom(buf_size)
    msg_tuple = struct.unpack('IbH',incoming_msg) #I = unsigned int, 4 bytes magic cookie, b = byte of offer msg, H = unsigned short, 2 bytes representing server port
    if msg_tuple[0] != magic_cookie or msg_tuple[1] != offer_op_code:
        return False
    udp_sock.close
    return (server_ip_address[0],msg_tuple[2]) #returning server's ip and server's tcp port  

def handleTCP(server_ip,server_port):
    """
    Creates a tcp connection with the server and returns the tcp socket for the game
    """
    tcp_sock = socket(AF_INET, SOCK_STREAM)
    tcp_sock.connect((server_ip,server_port))
    tcp_sock.send((team_name + "\n").encode())
    return tcp_sock

def read_from_stdin(tcp_socket):
    reads,_,_ = select.select([sys.stdin,[],[],10])
    if sys.stdin in reads:
        ans=sys.stdin.read(1)
        try:
            tcp_socket.send(ans.encode())
        except:
            pass
    
def gameMode(tcp_sock):
    """
    This function simulates the game via the tcp connection with the server
    """
    welcome_msg = tcp_sock.recv(buf_size).decode()
    print(welcome_msg)
    

    stdin_thread = threading.Thread(target=read_from_stdin,args=(tcp_sock, ))
    stdin_thread.start()
    response = tcp_sock.recv(buf_size).decode()
    
    print(response)



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
        gameMode(tcp_sock)
        is_first_cycle = False