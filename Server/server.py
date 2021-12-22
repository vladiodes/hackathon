from socket import *
import time


class Server:

    def __init__(self):
        self.name = socket.gethostname()
        self.ip = socket.gethostbyname(self.name)

    def run(self):
        print('Server started, listening on IP address {ip}'.format(ip=self.ip))
        server_UDP_socket = socket(AF_INET, SOCK_DGRAM)
        server_UDP_socket.bind('', 12000)
        while 1:
            time.sleep(1)
            message = makeOffer()
            server_UDP_socket.sendto(message, ('255.255.255.255', 13117))

