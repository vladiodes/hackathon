from socket import *
import threading
import time
import random
import struct

stop_threads = False
buffer_size=2<<10
winning_team = 0
lock = threading.Lock()


def create_math_problems():
    exercises = ["1 + 0", "1 + 1", "1 + 2", "1 + 3", "1 + 4", "1 + 5", "1 + 6", "1 + 7", "1 + 8"]
    answers = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    return exercises, answers


def play(player_socket,other_player_socket, expected_answer, group_number, opponent_group,win_msg,lose_msg):  # need to synchronize the threads
    global winning_team
    global lock
    player_socket.settimeout(10)
    try:
        answer = player_socket.recv(buffer_size).decode()
        if answer == expected_answer:
            lock.acquire()
            if winning_team==0:
                winning_team=group_number
                player_socket.send(win_msg.encode())
                other_player_socket.send(win_msg.encode())
            lock.release
        else:
            lock.acquire()
            if winning_team==0:
                winning_team=opponent_group
                player_socket.send(lose_msg.encode())
                other_player_socket.send(lose_msg.encode())
            lock.release
    except:
        pass


class Server:

    def __init__(self):
        self.name = gethostname()
        self.ip = gethostbyname(self.name)

    def run_udp(self, tcp_socket_port,is_first_cycle):
        if is_first_cycle:
            print('Server started, listening on IP address {ip}'.format(ip=self.ip))
        else:
            print('Game over, sending out offer requests...')

        # make the UDP message according to the format
        message = struct.pack('IbH',0xabcddcba,0x2,tcp_socket_port)

        # bind socket
        server_UDP_socket = socket(AF_INET, SOCK_DGRAM)
        server_UDP_socket.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
        server_UDP_socket.setsockopt(SOL_SOCKET,SO_BROADCAST,1)
        #server_UDP_socket.bind(('', 0))

        # send offer messages
        global stop_threads
        while not stop_threads:
            time.sleep(1)
            if not stop_threads:
                server_UDP_socket.sendto(message, ('255.255.255.255', 13117))
            else:
                server_UDP_socket.close()

    def run_server(self,is_first_cycle):

        global_vars = globals()

        # bind the socket
        server_TCP_socket = socket(AF_INET, SOCK_STREAM)
        server_TCP_socket.bind(('', 0))
        server_TCP_socket_port = (server_TCP_socket.getsockname())[1]

        # run the thread that will send offer messages over UDP while listening for connection requests over TCP
        global_vars['stop_threads'] = False
        udp_thread = threading.Thread(target=self.run_udp, args=(server_TCP_socket_port,is_first_cycle ))
        udp_thread.start()

        # listen for connection requests
        player1_socket = None
        player2_socket = None
        server_TCP_socket.listen(1)

        # accept new connections
        while (player1_socket is None) | (player2_socket is None):
            connectionSocket, address = server_TCP_socket.accept()
            if player1_socket is None:
                player1_socket = connectionSocket
            else:
                player2_socket = connectionSocket

        # 2 players have connected , stop accepting new players and stop sending offers
        server_TCP_socket.close()
        global_vars['stop_threads'] = True
        time.sleep(10)

        # get the group names, send welcome message
        group1_name = player1_socket.recv(buffer_size).decode()
        group2_name = player2_socket.recv(buffer_size).decode()
        exercises, answers = create_math_problems()
        exercise_number = random.randrange(0, len(exercises))
        exercise = exercises[exercise_number]
        exercise_answer = answers[exercise_number]
        message = "Welcome to Quick Maths\n" \
                      "Player 1: " + group1_name + \
                      "Player 2: " + group2_name + \
                      "==\n" \
                      "Please answer the following question as fast as you can\n" \
                      "How much is " + exercise + " ?"

        # make "Game Over" message
        msg = None

        # send welcome messages
        player1_socket.send(message.encode())
        player2_socket.send(message.encode())
                         

        # prepare threads for clients
        global_vars['stop_threads'] = False
        win_msg_player1 = "Game Over!\n" \
                        "The correct answer was " + exercise_answer + "!\n" \
                        "Congratulations to the winner: (GROUP 1) " + group1_name
        win_msg_player2 = "Game Over!\n" \
                        "The correct answer was " + exercise_answer + "!\n" \
                        "Congratulations to the winner: (GROUP 2) " + group2_name
        player1_thread = threading.Thread(target=play, args=(player1_socket,player2_socket, exercise_answer, 1, 2,win_msg_player1,win_msg_player2))
        player2_thread = threading.Thread(target=play, args=(player2_socket,player1_socket, exercise_answer, 2, 1,win_msg_player2,win_msg_player1))

        # start the threads
        player1_thread.start()
        player2_thread.start()

        player1_thread.join()
        player2_thread.join()

        if winning_team==0:
            msg = "Game Over!\n" \
                   "The correct answer was " + exercise_answer + "!\n" \
                   "The game ended in a draw"
            player1_socket.send(msg.encode())
            player2_socket.send(msg.encode())

if __name__ == "__main__":
    is_first_cycle = True
    while True:
        Server().run_server(is_first_cycle)
        is_first_cycle = False
