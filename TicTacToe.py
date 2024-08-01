import random
from typing import Literal


class TicTacToe:

    computer = 1  # 表示电脑的代号，1代表电脑
    human = -1  # 表示人类玩家的代号，-1代表人类

    def __init__(self):
        # 初始化棋盘，3x3的二维列表，初始值为0，表示空位
        self._board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    def force_move(
        self, row: Literal[0, 1, 2], col: Literal[0, 1, 2], player: Literal[-1, 1]
    ):
        """强制落子"""
        self._board[row][col] = player

    def manual_move(self, row: Literal[0, 1, 2], col: Literal[0, 1, 2]):
        """人类落子"""
        # 检查指定位置是否为空位（值为0）
        if row in range(3) and col in range(3) and self._board[row][col] == 0:
            # 如果为空位，则在该位置落人类的子（值为-1）
            self._board[row][col] = self.human
            # 返回True表示落子成功
            return True
        # 如果该位置已被占用，返回 False 表示落子失败
        return False

    def auto_move(self):
        """自动落子"""
        # 找到最佳落子位置
        move = self.find_best_move()
        # 如果找到合适的空位
        if move:
            row, col = move
            # 在该位置落电脑的子（值为1）
            self._board[row][col] = self.computer
            # 返回落子位置
            return move
        # 如果没有合适的位置，返回None
        return None

    def try_update_board(self, new_board: list[list[int]]):
        """尝试更新棋盘，识别非法操作，并给出撤销非法操作的方案"""
        if len(new_board) != 3 or any(len(row) != 3 for row in new_board):
            return False, None

        new_human_moves = []  # 识别到的新增人类棋子 (row, col)
        new_computer_moves = []  # 识别到的新增电脑棋子，视为异常落子 (row, col)
        removed_pieces = []  # 识别到的被移除的棋子 (row, col, player_from)
        replaced_pieces = []  # 识别到的被替换的棋子 (row, col, player_from)

        # 遍历行索引，范围为0到2（包含0和2）
        for i in range(3):
            # 遍历列索引，范围为0到2（包含0和2）
            for j in range(3):
                # 检查当前棋盘与新的棋盘是否存在差异
                if self._board[i][j] != new_board[i][j]:
                    # 如果当前棋盘的此位置上没有棋子（即为0）
                    if self._board[i][j] == 0:
                        # 如果在新棋盘上，此位置上为电脑棋子
                        if new_board[i][j] == self.computer:
                            # 记录新增加的电脑棋子的位置
                            new_computer_moves.append((i, j))
                        # 如果在新棋盘上，此位置上为人类棋子
                        elif new_board[i][j] == self.human:
                            # 记录新增加的人类棋子的位置
                            new_human_moves.append((i, j))
                    # 如果当前棋盘的此位置上有棋子（不为0）
                    else:
                        # 如果在新棋盘上，此位置上为空（即变为0）
                        if new_board[i][j] == 0:
                            # 记录移除掉的棋子及其位置和类型
                            removed_pieces.append((i, j, self._board[i][j]))
                        # 如果在新棋盘上，此位置上变为另一个棋子
                        else:
                            # 记录被替换掉的棋子及其位置和类型
                            replaced_pieces.append((i, j, self._board[i][j]))

        to_move_actions = (
            []
        )  # 通知机械臂撤销棋盘落子位置所需做出的动作 (from_row, from_col, target_row, target_col)，row == -1 代表从棋子堆中取棋子或将棋子放回棋子堆，在这种情况下 col 指示棋子类型

        # 1. 处理棋盘内的移动
        # 遍历所有被移除的棋子，使用切片创建副本进行迭代，这样可以在迭代过程中对原列表进行修改而不影响循环
        for removed in removed_pieces[:]:
            # 遍历所有新的人的移动和新的计算机的移动
            for new_move in new_human_moves + new_computer_moves:
                # 如果被移除的棋子在新的棋局中找到了对应的新位置（判断移除的棋子类型与新位置的棋子类型相同）
                if removed[2] == new_board[new_move[0]][new_move[1]]:
                    # 将新的位置和被移除的旧位置作为一个动作添加到待移动动作列表中
                    to_move_actions.append(
                        (new_move[0], new_move[1], removed[0], removed[1])
                    )
                    # 如果这个新的移动属于人的移动列表，则从人的移动列表中删除该移动
                    if new_move in new_human_moves:
                        new_human_moves.remove(new_move)
                    # 否则，从计算机的移动列表中删除该移动
                    else:
                        new_computer_moves.remove(new_move)

                    # 从被移除的棋子列表中删除该棋子（因为已经处理过了）
                    removed_pieces.remove(removed)
                    # 退出当前循环，因为我们已经找到并处理了这个被移除的棋子
                    break

        # 2. 处理被替换的棋子
        for row, col, player_from in replaced_pieces:
            # 先将新的棋子放入棋子堆
            to_move_actions.append((row, col, -1, -player_from))
            # 再将原来的棋子放回原位
            to_move_actions.append((-1, player_from, row, col))

        # 3. 处理新增的电脑棋子（移回棋子堆）
        for row, col in new_computer_moves:
            to_move_actions.append((row, col, -1, self.computer))

        # 4. 处理剩余的被移除棋子（放回原位）
        for row, col, player_from in removed_pieces:
            to_move_actions.append((-1, player_from, row, col))

        # 确定更新是否有效
        is_valid = len(new_human_moves) == 1 and len(to_move_actions) == 0

        # 如果操作无效，将所有新的人类落子移回棋堆
        if not is_valid:
            for row, col in new_human_moves:
                if (row, col, -1, self.human) not in to_move_actions:
                    to_move_actions.append((row, col, -1, self.human))

        if is_valid:
            self._board = new_board[:]

        return is_valid, None if is_valid else to_move_actions

    def force_update_board(self, new_board):
        """强制刷新棋盘"""
        if len(new_board) != 3 or any(len(row) != 3 for row in new_board):
            return False
        self._board = [row[:] for row in new_board]
        return True

    def reset_board(self):
        """重置棋盘"""
        self._board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    def find_best_move(self, player=computer):
        """寻找最佳落子位置"""
        # 检查是否有获胜机会
        winning_move = self.find_winning_move(player)
        if winning_move:
            return winning_move

        # 检查是否需要阻止对手获胜
        blocking_move = self.find_winning_move(-player)
        if blocking_move:
            return blocking_move

        # 如果中心格子为空,优先占据中心
        if self._board[1][1] == 0:
            return (1, 1)

        # 检测是否是第四步
        if sum(sum(cell != 0 for cell in row) for row in self._board) == 3:
            # 检测是否是棱+对角
            if self._board[0][1] == -player:
                if self._board[2][0] == -player:
                    if self._board[0][0] == 0:
                        return (0, 0)
                elif self._board[2][2] == -player:
                    if self._board[0][2] == 0:
                        return (0, 2)
            elif self._board[1][0] == -player:
                if self._board[0][2] == -player:
                    if self._board[0][0] == 0:
                        return (0, 0)
                elif self._board[2][2] == -player:
                    if self._board[2][0] == 0:
                        return (2, 0)
            elif self._board[1][2] == -player:
                if self._board[0][0] == -player:
                    if self._board[0][2] == 0:
                        return (0, 2)
                elif self._board[2][0] == -player:
                    if self._board[2][2] == 0:
                        return (2, 2)
            elif self._board[2][1] == -player:
                if self._board[0][0] == -player:
                    if self._board[2][0] == 0:
                        return (2, 0)
                elif self._board[0][2] == -player:
                    if self._board[2][2] == 0:
                        return (2, 2)

            # 检测是否是电脑中心
            if self._board[1][1] == player:
                # 检测是否是对角
                edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
                if self._board[0][0] == -player and self._board[2][2] == -player:
                    return random.choice(edges)
                elif self._board[0][2] == -player and self._board[2][0] == -player:
                    return random.choice(edges)

                # 再检测是否是相邻的棱
                if self._board[0][1] == -player and self._board[1][0] == -player:
                    return (0, 0)
                elif self._board[0][1] == -player and self._board[1][2] == -player:
                    return (0, 2)
                elif self._board[1][0] == -player and self._board[2][1] == -player:
                    return (2, 0)
                elif self._board[1][2] == -player and self._board[2][1] == -player:
                    return (2, 2)

        # 尝试占据角落或边缘，加入随机性
        empty_positions = []
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        edges = [(0, 1), (1, 0), (1, 2), (2, 1)]

        for corner in corners:
            if self._board[corner[0]][corner[1]] == 0:
                empty_positions.append(corner)

        if empty_positions:
            return random.choice(empty_positions)

        for edge in edges:
            if self._board[edge[0]][edge[1]] == 0:
                empty_positions.append(edge)

        if empty_positions:
            return random.choice(empty_positions)

        # 如果没有可用的位置,返回None
        return None

    def find_winning_move(self, player):
        # 检查所有空位置,看是否有获胜机会
        for i in range(3):
            for j in range(3):
                if self._board[i][j] == 0:
                    self._board[i][j] = player
                    if self.check_win(player):
                        self._board[i][j] = 0  # 恢复棋盘
                        return (i, j)
                    self._board[i][j] = 0  # 恢复棋盘
        return None

    def check_win(self, player):
        # 检查行
        for row in self._board:
            if all(cell == player for cell in row):
                return True

        # 检查列
        for col in range(3):
            if all(self._board[row][col] == player for row in range(3)):
                return True

        # 检查对角线
        if all(self._board[i][i] == player for i in range(3)):
            return True
        if all(self._board[i][2 - i] == player for i in range(3)):
            return True

        return False

    def check_winner(self):
        for player in [self.computer, self.human]:
            if self.check_win(player):
                return player
        return 0

    def is_board_full(self):
        """检查棋盘是否已满"""
        return all(all(cell != 0 for cell in row) for row in self._board)

    def get_board(self):
        """获取当前棋盘状态"""
        return [row[:] for row in self._board]

    def print_board(self, file=None):
        """打印棋盘"""

        def to_char(cell):
            return "X" if cell == 1 else "O" if cell == -1 else " "

        print("  0 1 2", file=file)
        for i, row in enumerate(self._board):
            print(i, end=" ", file=file)
            for cell in row:
                print(to_char(cell), end=" ", file=file)
            print(file=file)


if __name__ == "__main__":
    # 初始化三子棋
    ttt = TicTacToe()

    first = input("1 -> 电脑先手；-1 -> 玩家先手：")
    player = TicTacToe.human if first == "-1" else TicTacToe.computer

    # 游戏主循环
    while True:
        ttt.print_board()
        lastBoard = ttt.get_board()

        if player == -1:
            # 玩家回合
            while True:
                try:
                    row, col = map(int, input("请输入落子位置（行,列）：").split(","))
                    if ttt.manual_move(row, col):
                        break
                    else:
                        print("无效的位置，请重新选择。")
                except ValueError:
                    print("请输入有效的数字。")
        else:
            # 电脑回合
            move = ttt.auto_move()
            if move:
                row, col = move
                if lastBoard[row][col] == 0:
                    lastBoard[row][col] = player
                    print(f"电脑选择落子位置：({row}, {col})")
                else:
                    print("电脑选择的位置已有棋子，游戏结束。")
                    break
            else:
                print("电脑无法做出有效选择，游戏结束。")
                break

        # 检查是否有人获胜
        winner = ttt.check_winner()
        if winner != 0:
            ttt.print_board()
            print("玩家获胜！" if winner == -1 else "电脑获胜！")
            break

        # 检查是否平局
        if ttt.is_board_full():
            ttt.print_board()
            print("游戏结束，平局！")
            break

        # 切换玩家
        player = -player

    # print("游戏结束！")
