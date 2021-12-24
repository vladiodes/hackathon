from socket import *
import threading
import time
import random
import struct

stop_threads = False


def create_math_problems():
    exercises = ["1 + 0", "1 + 1", "1 + 2", "1 + 3", "1 + 4", "1 + 5", "1 + 6", "1 + 7", "1 + 8"]
    answers = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    return exercises, answers


def play(player_socket, expected_answer, group_number, opponent_group):  # need to synchronize the threads

    global_vars = globals()

    global stop_threads
    while not stop_threads:
        answer = player_socket.recv(4).decode()
        global_vars['stop_threads'] = True
        if answer == expected_answer:
            player_socket.send(group_number.tobytes(4, 'big'))
        else:
            player_socket.send(opponent_group.tobytes(4, 'big'))


class Server:

    def __init__(self):
        self.name = gethostname()
        self.ip = gethostbyname(self.name)

    def run_udp(self, tcp_socket_port):
        print('Server started, listening on IP address {ip}'.format(ip=self.ip))

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

    def run_server(self):

        global_vars = globals()

        # bind the socket
        server_TCP_socket = socket(AF_INET, SOCK_STREAM)
        server_TCP_socket.bind(('', 0))
        server_TCP_socket_port = (server_TCP_socket.getsockname())[1]

        # run the thread that will send offer messages over UDP while listening for connection requests over TCP
        global_vars['stop_threads'] = False
        udp_thread = threading.Thread(target=self.run_udp, args=(server_TCP_socket_port, ))
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
        group1_name = player1_socket.recv(1024).decode()
        group2_name = player2_socket.recv(1024).decode()
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
        game_over_txt = "Game Over!\n" \
                        "The correct answer was {answer:ans}!\n" \
                        "Congratulations to the winner: {winning_group:name}"
        draw_txt = "Game Over!\n" \
                   "The correct answer was {answer:ans}!\n" \
                   "The game ended in a draw"
        msg = None

        # send welcome messages
        player1_socket.send(message.encode())
        player2_socket.send(message.encode())

        # prepare threads for clients
        global_vars['stop_threads'] = False
        player1_thread = threading.Thread(target=play, args=(player1_socket, exercise_answer, 1, 2))
        player2_thread = threading.Thread(target=play, args=(player2_socket, exercise_answer, 2, 1))

        # start the threads
        player1_thread.start()
        player2_thread.start()

        # now we decide the winner
        try:
            threading.Condition.wait_for(lambda: global_vars['stop_threads'], timeout=10)
            # someone has written , try reading from player 1 then from player 2
            player1_socket.settimeout(0)
            player2_socket.settimeout(0)
            try:
                winner = player1_socket.recv(4).decode()
                # create message
                msg = game_over_txt.format(answer=exercise_answer, winning_group=winner)
            except TimeoutError:
                winner = player2_socket.recv(4).decode()
                # create message
                msg = game_over_txt.format(answer=exercise_answer, winning_group=winner)
        except TimeoutError:
            # create draw message
            msg = draw_txt

        player1_socket.settimeout(None)
        player2_socket.settimeout(None)

        player1_socket.send(msg)
        player2_socket.send(msg)


if __name__ == "__main__":
    Server().run_server()
