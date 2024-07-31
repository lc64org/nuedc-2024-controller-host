import random
from typing import List, Optional, Tuple


# 棋局控制系统类
class ChessControlSystem:
    # 初始化方法
    def __init__(self, opencv_instance, tictactoe_instance, communication_instance):
        self.opencv = opencv_instance  # OpenCV实例，用于图像处理
        self.tictactoe = tictactoe_instance  # 井字棋实例，用于游戏逻辑
        self.comm = communication_instance  # 通信实例，用于与机器人手臂通信

        self.computer_color = None  # 电脑的棋子颜色
        self.human_color = None  # 人类的棋子颜色
        self.computer_pile = []  # 电脑的棋堆
        self.human_pile = []  # 人类的棋堆
        self.empty_positions = list(range(9))  # 棋盘上空位的列表

    # 设置棋子颜色
    def set_colors(self, computer_color: str):
        self.computer_color = computer_color  # 设置电脑的棋子颜色
        self.human_color = (
            "black" if computer_color == "white" else "white"
        )  # 根据电脑颜色设置人类的棋子颜色

    # 更新棋堆
    def update_piles(self):
        self.computer_pile = []  # 清空电脑的棋堆
        self.human_pile = []  # 清空人类的棋堆
        self.empty_positions = list(range(9))  # 重置空位列表

        # 遍历所有棋子的信息，并根据位置更新棋堆和空位列表
        for piece in self.opencv.get_pieces_info():
            color, position, x, y = piece
            if position == -1:  # 棋子不在棋盘上
                if color == self.computer_color:  # 是电脑的棋子
                    self.computer_pile.append((x, y))  # 添加到电脑的棋堆
                else:  # 是人类的棋子
                    self.human_pile.append((x, y))  # 添加到人类的棋堆
            elif position >= 0:  # 棋子在棋盘上
                if position in self.empty_positions:  # 如果位置在空位列表中
                    self.empty_positions.remove(position)  # 移除该空位

    # 将OpenCV坐标转换为棋盘位置
    def opencv_to_board_position(self, x: float, y: float) -> Tuple[int, int]:
        # 此函数是一个占位符，需要实现实际的转换逻辑
        pass

    # 将棋盘位置转换为OpenCV坐标
    def board_to_opencv_position(self, row: int, col: int) -> Tuple[float, float]:
        # 此函数是一个占位符，需要实现实际的转换逻辑
        pass

    # 移动棋子
    def move_piece(self, from_pos: Tuple[float, float], to_pos: Tuple[float, float]):
        # 控制机器人手臂将棋子从一个位置移动到另一个位置
        # 此函数是一个占位符，需要实现实际的移动逻辑
        x1, y1 = from_pos
        x2, y2 = to_pos
        self.comm.send_command(True, True, True, True, x1, y1, 0)  # 拾起棋子
        self.comm.send_command(True, True, True, True, x2, y2, 0)  # 放置棋子

    # 更新棋盘
    def update_board(self):
        current_board = self.opencv.get_board_state()  # 获取当前棋盘状态
        valid, operations = self.tictactoe.try_update_board(
            current_board
        )  # 尝试更新井字棋的棋盘状态

        if valid:  # 如果更新有效
            self.update_piles()  # 更新棋堆
        else:  # 如果更新无效
            for op in operations:  # 遍历所有操作
                row_from, col_from, row_to, col_to = op
                if row_from == -1:  # 从棋堆中移动棋子
                    pile = (
                        self.computer_pile if col_from == 1 else self.human_pile
                    )  # 根据颜色选择棋堆
                    from_pos = pile.pop()  # 从棋堆中取出一枚棋子
                else:  # 从棋盘上移动棋子
                    from_pos = self.board_to_opencv_position(
                        row_from, col_from
                    )  # 获取棋子的OpenCV位置

                to_pos = self.board_to_opencv_position(
                    row_to, col_to
                )  # 获取目标位置的OpenCV坐标
                self.move_piece(from_pos, to_pos)  # 移动棋子

                if row_from == -1:  # 如果是从棋堆中移动棋子
                    self.update_piles()  # 更新棋堆

        return valid  # 返回更新是否有效

    # 电脑移动棋子
    def computer_move(self):
        row, col = self.tictactoe.auto_move()  # 获取电脑的自动移动位置
        to_pos = self.board_to_opencv_position(row, col)  # 获取目标位置的OpenCV坐标
        from_pos = self.computer_pile.pop()  # 从电脑的棋堆中取出一枚棋子
        self.move_piece(from_pos, to_pos)  # 移动棋子
        self.empty_positions.remove(row * 3 + col)  # 移除目标位置的空位

    # 检查游戏状态
    def check_game_status(self) -> str:
        winner = self.tictactoe.check_winner()  # 检查是否有赢家
        if winner == 1:
            return "Computer wins!"  # 电脑胜利
        elif winner == -1:
            return "Human wins!"  # 人类胜利
        elif self.tictactoe.is_board_full():  # 棋盘满了没有空位
            return "It's a draw!"  # 平局
        return "Game in progress"  # 游戏进行中

    # 按钮1的回调函数
    def button1_callback(self):
        """Move any black piece to the center of the board"""
        if not self.human_pile:  # 如果人类的棋堆没有棋子
            print("No black pieces available in the pile")
            return

        from_pos = self.human_pile.pop()  # 从人类的棋堆中取出一枚棋子
        to_pos = self.board_to_opencv_position(1, 1)  # 棋盘中心的位置
        self.move_piece(from_pos, to_pos)  # 移动棋子
        self.empty_positions.remove(4)  # 移除中心位置的空位
        self.update_board()  # 更新棋盘

    # 按钮2的回调函数
    def button2_callback(self):
        """Interactive movement of pieces"""
        for _ in range(2):  # 人类移动两次
            if not self.human_pile:  # 如果人类的棋堆没有棋子
                print("No more black pieces available")
                break
            from_pos = self.human_pile.pop()  # 从人类的棋堆中取出一枚棋子
            to_pos = self.board_to_opencv_position(
                random.choice(self.empty_positions) // 3,
                random.choice(self.empty_positions) % 3,
            )
            self.move_piece(from_pos, to_pos)  # 移动棋子
            self.update_board()  # 更新棋盘

        for _ in range(2):  # 电脑移动两次
            if not self.computer_pile:  # 如果电脑的棋堆没有棋子
                print("No more white pieces available")
                break
            from_pos = self.computer_pile.pop()  # 从电脑的棋堆中取出一枚棋子
            to_pos = self.board_to_opencv_position(
                random.choice(self.empty_positions) // 3,
                random.choice(self.empty_positions) % 3,
            )
            self.move_piece(from_pos, to_pos)  # 移动棋子
            self.update_board()  # 更新棋盘

    # 按钮3的回调函数
    def button3_callback(self):
        """Computer (黑) vs Human (白) game"""
        self.set_colors("black")  # 设置电脑为黑棋
        self.update_piles()  # 更新棋堆

        while True:  # 一直循环直到游戏结束
            self.computer_move()  # 电脑移动棋子
            if self.check_game_status() != "Game in progress":  # 检查游戏状态
                break

            if not self.update_board():  # 更新棋盘
                print("Invalid human move. Game ended.")
                break

            if self.check_game_status() != "Game in progress":  # 检查游戏状态
                break

        print(self.check_game_status())  # 打印游戏结果

    # 按钮4的回调函数
    def button4_callback(self):
        """Human (黑) vs Computer (白) game"""
        self.set_colors("white")  # 设置电脑为白棋
        self.update_piles()  # 更新棋堆

        while True:  # 一直循环直到游戏结束
            if not self.update_board():  # 更新棋盘
                print("Invalid human move. Game ended.")
                break

            if self.check_game_status() != "Game in progress":  # 检查游戏状态
                break

            self.computer_move()  # 电脑移动棋子
            if self.check_game_status() != "Game in progress":  # 检查游戏状态
                break

        print(self.check_game_status())  # 打印游戏结果

    # 按钮5的回调函数
    def button5_callback(self):
        """Clear the board and reset pieces"""
        # 将所有棋子移回各自的棋堆
        for piece in self.opencv.get_pieces_info():
            color, position, x, y = piece
            if position >= 0:  # 如果棋子在棋盘上
                to_pile = (
                    self.computer_pile
                    if color == self.computer_color
                    else self.human_pile
                )
                to_pos = (
                    to_pile[0][0],
                    to_pile[0][1] + len(to_pile) * 0.05,
                )  # 根据棋堆高度调整Y坐标
                self.move_piece((x, y), to_pos)  # 移动棋子
                to_pile.append(to_pos)  # 将位置添加到棋堆

        self.update_piles()  # 更新棋堆
        self.tictactoe = type(self.tictactoe)()  # 重置井字棋实例
