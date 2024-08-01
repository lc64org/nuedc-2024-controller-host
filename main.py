import random
import time
from queue import Queue
from threading import Lock, Thread
from typing import Tuple

import cv2

from ChessBoardProcessor import ChessBoardProcessor
from SerialCommunicator import SerialCommunicator
from TicTacToe import TicTacToe
from transform import camera_to_robot


class ChessControlSystem:
    def __init__(
        self,
        processor_instance: ChessBoardProcessor,
        tictactoe_instance: TicTacToe,
        communication_instance: SerialCommunicator,
    ):
        self.processor = processor_instance
        self.tictactoe = tictactoe_instance
        self.comm = communication_instance

        self.computer_color = None
        self.human_color = None
        self.computer_pile = []
        self.human_pile = []
        self.empty_positions = list(range(9))

        self.lock = Lock()
        self.command_queue = Queue()

    def set_colors(self, computer_color: str):
        # with self.lock:
        self.computer_color = computer_color
        self.human_color = "black" if computer_color == "white" else "white"

    def update_piles(self):
        # 使用锁机制确保线程安全
        # with self.lock:
        # 初始化电脑方和人类方的棋子堆
        self.computer_pile = []  # 电脑方的棋子堆
        self.human_pile = []  # 人类方的棋子堆
        # 初始化空位列表，棋盘上0到8共9个位置
        self.empty_positions = list(range(9))

        # 从处理器中获取棋子信息
        for piece in self.processor.get_pieces_info():
            color, position, x, y = piece  # 解包棋子信息
            if position == -1:  # 棋子未在棋盘上，处于待入场状态
                if color == self.computer_color:
                    # 电脑方的棋子加入电脑堆
                    self.computer_pile.append((x, y))
                else:
                    # 人类方的棋子加入人类堆
                    self.human_pile.append((x, y))
            else:
                # 如果棋子已经在棋盘上，移除该位置标记为非空
                if position in self.empty_positions:
                    self.empty_positions.remove(position)

    def move_piece(self, from_pos: Tuple[float, float], to_pos: Tuple[float, float]):
        # 解包起始位置和目标位置的坐标
        x1, y1 = from_pos
        x2, y2 = to_pos
        # 定义移动棋子的命令队列
        commands = [
            (True, True, False, True, x1, y1, 60),  # 起始位置按下
            (True, True, True, True, x1, y1, 45),  # 起始位置移动
            (True, True, True, True, x1, y1, 60),  # 起始位置保持按下状态
            (True, True, True, True, x2, y2, 60),  # 移动到目标位置
            (True, True, False, True, x2, y2, 60),  # 目标位置松开
        ]
        # 将每条命令放入命令队列
        for cmd in commands:
            self.comm.send_command(*cmd)

    def update_board(self):
        with self.lock:
            current_board = self.processor.get_board_state()
            valid, operations = self.tictactoe.try_update_board(current_board)

            if valid:
                self.update_piles()
            else:
                for op in operations:
                    row_from, col_from, row_to, col_to = op
                    if row_from == -1:
                        pile = self.computer_pile if col_from == 1 else self.human_pile
                        from_pos = pile.pop()
                    else:
                        from_pos = self.board_to_opencv_position(row_from, col_from)

                    to_pos = self.board_to_opencv_position(row_to, col_to)
                    self.move_piece(from_pos, to_pos)

                    if row_from == -1:
                        self.update_piles()

            return valid

    def computer_move(self):
        with self.lock:
            row, col = self.tictactoe.auto_move()
            to_pos = self.board_to_opencv_position(row, col)
            from_pos = self.computer_pile.pop()
            self.move_piece(from_pos, to_pos)
            self.empty_positions.remove(row * 3 + col)

    def check_game_status(self) -> str:
        with self.lock:
            winner = self.tictactoe.check_winner()
            if winner == 1:
                return "Computer wins!"
            elif winner == -1:
                return "Human wins!"
            elif self.tictactoe.is_board_full():
                return "It's a draw!"
            return "Game in progress"

    def function1_callback(self):
        # 移动黑棋到中心位置
        print("Function 1 callback")
        # self.set_colors("white")
        # # with self.lock:
        # print("Function 1 callback with lock")
        # self.update_piles()

        # if not self.human_pile:
        #     print("No black pieces available in the pile")
        #     return

        # # from_pos = self.human_pile.pop()
        # toX, toY = self.processor.grid_centers[4]
        # # to_pos = camera_to_robot(toX, toY)
        # # self.move_piece(from_pos, to_pos)
        self.move_piece((220, -60), (180, 8))
        # self.empty_positions.remove(4)
        # self.update_board()
        self.comm.send_command(True, True, False, True, 0, 0, 0)

    def function2_callback(self):
        # with self.lock:
        positions = input("Enter positions: ").split(",")
        if len(positions) != 4:
            print("Invalid input")
            return

        pos0 = self.processor.grid_centers[positions[0]]
        pos1 = self.processor.grid_centers[positions[1]]
        pos2 = self.processor.grid_centers[positions[2]]
        pos3 = self.processor.grid_centers[positions[3]]

        self.move_piece((248, -79), pos0)
        self.move_piece((220, -82), pos1)
        self.move_piece((249, 91), pos2)
        self.move_piece((220, 90), pos3)
        # for _ in range(2):
        #     if not self.human_pile:
        #         print("No more black pieces available")
        #         break
        #     from_pos = self.human_pile.pop()
        #     to_pos = self.board_to_opencv_position(
        #         random.choice(self.empty_positions) // 3,
        #         random.choice(self.empty_positions) % 3,
        #     )
        #     self.move_piece(from_pos, to_pos)
        #     self.update_board()

        # for _ in range(2):
        #     if not self.computer_pile:
        #         print("No more white pieces available")
        #         break
        #     from_pos = self.computer_pile.pop()
        #     to_pos = self.board_to_opencv_position(
        #         random.choice(self.empty_positions) // 3,
        #         random.choice(self.empty_positions) % 3,
        #     )
        #     self.move_piece(from_pos, to_pos)
        #     self.update_board()

    def button3_callback(self):
        self.set_colors("black")
        self.update_piles()

        while True:
            self.computer_move()
            if self.check_game_status() != "Game in progress":
                break

            if not self.update_board():
                print("Invalid human move. Game ended.")
                break

            if self.check_game_status() != "Game in progress":
                break

        print(self.check_game_status())

    def button4_callback(self):
        self.set_colors("white")
        self.update_piles()

        while True:
            if not self.update_board():
                print("Invalid human move. Game ended.")
                break

            if self.check_game_status() != "Game in progress":
                break

            self.computer_move()
            if self.check_game_status() != "Game in progress":
                break

        print(self.check_game_status())

    def button5_callback(self):
        with self.lock:
            for piece in self.processor.get_pieces_info():
                color, position, x, y = piece
                if position >= 0:
                    to_pile = (
                        self.computer_pile
                        if color == self.computer_color
                        else self.human_pile
                    )
                    to_pos = (to_pile[0][0], to_pile[0][1] + len(to_pile) * 0.05)
                    self.move_piece((x, y), to_pos)
                    to_pile.append(to_pos)

            self.update_piles()
            self.tictactoe = type(self.tictactoe)()

    def main_thread(self):
        while True:
            if not self.command_queue.empty():
                command = self.command_queue.get()
                self.comm.send_command(*command)
            time.sleep(0.1)

    def opencv_thread(self):
        cap = cv2.VideoCapture(2)
        cap.set(cv2.CAP_PROP_EXPOSURE, -5.98)

        if not cap.isOpened():
            print("Error: Could not open video capture.")
        else:

            self.processor.createControllerWindow()
            self.processor.registerControllerCallback(
                self.processor.MOVE_BLACK_CHESSES_TO_CENTER,
                self.function1_callback,
            )
            self.processor.registerControllerCallback(
                self.processor.MOVE_TWO_BLACK_TWO_WHITE,
                self.function2_callback,
            )

            while True:
                ret, img = cap.read()
                if not ret:
                    print("Error: Could not read frame.")
                    break
                image = img.copy()
                with self.lock:
                    self.processor.process_frame(image)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                time.sleep(0.1)

            cap.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    processor = ChessBoardProcessor()
    tictactoe = TicTacToe()
    communicator = SerialCommunicator()
    communicator.connect()

    chess_system = ChessControlSystem(processor, tictactoe, communicator)

    opencv_thread = Thread(target=chess_system.opencv_thread)
    main_thread = Thread(target=chess_system.main_thread)

    opencv_thread.start()
    main_thread.start()

    opencv_thread.join()
    # main_thread.join()
