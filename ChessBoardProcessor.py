import cv2
import numpy as np


class ChessBoardProcessor:

    # 黑色空闲棋子放置区坐标
    black_stay_position_coordinates = [
        (120, 145),
        (120, 180),
        (120, 215),
        (120, 250),
        (120, 285),
    ]
    # 白色空闲棋子放置区坐标
    white_stay_position_coordinates = [
        (365, 145),
        (365, 180),
        (365, 215),
        (365, 250),
        (365, 285),
    ]

    # 四个功能的 ID
    MOVE_BLACK_CHESSES_TO_CENTER = 1
    MOVE_TWO_BLACK_TWO_WHITE = 2
    COMPUTER_BLACK_FIRST = 3
    HUMAN_BLACK_FIRST = 4

    def __init__(self):
        # 初始化不在格子中的白色棋子的坐标列表
        self.white_coordinates = []
        # 初始化不在格子中的黑色棋子的坐标列表
        self.black_coordinates = []

        # 初始化在格子中的白色棋子坐标列表
        self.white_chess_coordinates = []
        # 初始化在格子中的黑色棋子坐标列表
        self.black_chess_coordinates = []

        # 初始化在格子中的白色棋子相对于棋盘顶点的坐标列表
        self.white_rot_coordinates = []
        # 初始化在格子中的黑色棋子相对于棋盘顶点的坐标列表
        self.black_rot_coordinates = []

        # 初始化棋盘的3x3网格，全部值设为0
        self.grid = np.zeros((3, 3), dtype=int)

        # 初始化网格中心点列表
        self.grid_centers = []

        self.controller = {
            "windowInitialized": False,
            "selectedFunction": 0,
            "functionCallback": {},
        }

    def get_pieces_info(self):
        """获取棋子信息，返回白色棋子坐标列表和黑色棋子坐标列表"""
        # color, position, x, y  position -1 为棋堆，0-8 为棋盘
        pieces_info = []
        for white_coordinate in self.white_coordinates:
            pieces_info.append(("white", -1, white_coordinate[0], white_coordinate[1]))
        for black_coordinate in self.black_coordinates:
            pieces_info.append(("black", -1, black_coordinate[0], black_coordinate[1]))
        for id, white_chess_coordinate in enumerate(self.white_chess_coordinates):
            pieces_info.append(
                (
                    "white",
                    self.white_rot_coordinates[id][2],
                    white_chess_coordinate[0],
                    white_chess_coordinate[1],
                )
            )
        for id, black_chess_coordinate in enumerate(self.black_chess_coordinates):
            pieces_info.append(
                (
                    "black",
                    self.black_rot_coordinates[id][2],
                    black_chess_coordinate[0],
                    black_chess_coordinate[1],
                )
            )
        return pieces_info

    def registerControllerCallback(self, functionId, callback):
        self.controller["functionCallback"][functionId] = callback

    def functionSelectionCallback(self, value):
        self.controller["selectedFunction"] = value

    def functionConfirmCallback(self, value):
        if value == 1:
            functionId = self.controller["selectedFunction"]
            if functionId in self.controller["functionCallback"]:
                self.controller["functionCallback"][functionId]()
            else:
                print("No callback function registered for function %s." % functionId)
            # 重置确认滑动条的值
            cv2.setTrackbarPos("Confirm", "Controller", 0)

    def createControllerWindow(self):
        if self.controller["windowInitialized"]:
            return
        cv2.namedWindow("Controller", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Controller", 400, 200)
        # 滑动条 1 选择功能，滑动条 2 确认
        # 功能 0. 无 1. 落黑子到中心 2. 落两黑两白 3. 电脑黑棋先手对弈 4. 人类黑棋先手对弈
        cv2.createTrackbar(
            "Function", "Controller", 0, 4, self.functionSelectionCallback
        )
        cv2.createTrackbar("Confirm", "Controller", 0, 1, self.functionConfirmCallback)
        self.controller["windowInitialized"] = True

    def coordinates_transformation(self, rotation_matrix, coordinate_x, coordinate_y):
        # 将2x2旋转矩阵扩展为3x3旋转矩阵
        rotation_matrix_3x3 = np.vstack([rotation_matrix, [0, 0, 1]])
        # 创建齐次坐标
        homogeneous_coordinate = np.array([coordinate_x, coordinate_y, 1])
        # 应用旋转矩阵进行坐标转换
        rotated_coordinate = np.dot(rotation_matrix_3x3, homogeneous_coordinate)
        # 提取转换后的x和y坐标
        rotated_x = rotated_coordinate[0]
        rotated_y = rotated_coordinate[1]
        return rotated_x, rotated_y

    def draw_circle(self, image, coordinates, color):
        # 在图像上绘制圆圈
        for coordinate in coordinates:
            # 确保坐标包含x, y和半径
            if len(coordinate) == 3:
                x, y, radius = coordinate
                # 确保圆的中心在图像范围内
                if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                    # 画圆圈的轮廓
                    cv2.circle(image, (int(x), int(y)), radius, color, 2)
                    # 画圆心
                    cv2.circle(image, (int(x), int(y)), 2, color, 3)

    def the_chess_real_sit(self, a, b):
        # 根据输入坐标计算实际棋子的坐标
        x = 100 - 0.896 * a
        y = 200 - 0.896 * b
        return x, y

    def the_square_real_sit(self, c, d):
        # 根据输入坐标计算实际方块的坐标
        x = 100 - 0.896 * c
        y = 200 - 0.896 * d
        return x, y

    def keep_point_order(self, points):
        # 计算所有点的中心点
        center = np.mean(points, axis=0)
        # 计算每个点与中心点的角度
        angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
        # 根据角度进行排序
        sort_idx = np.argsort(angles)
        return points[sort_idx]

    def summarize_chess_info(self, grid_centers, white_positions, black_positions):
        summary = []
        # 遍历每个网格中心点
        for i, center in enumerate(grid_centers):
            # 计算当前中心点所在的行列
            row, col = i // 3, i % 3
            # 初始化棋子信息字典
            chess_info = {
                "格子中心坐标": center,
                "棋子颜色": "无",
                "棋子坐标": "无",
                "是否在棋盘上": "否",
            }

            # 检查当前位置是否有白色棋子
            if (row, col) in white_positions:
                chess_info["棋子颜色"] = "白色"
                # 找到具体白色棋子的位置
                index = white_positions.index((row, col))
                chess_info["棋子坐标"] = self.white_rot_coordinates[index]
                chess_info["是否在棋盘上"] = "是"

            # 检查当前位置是否有黑色棋子
            elif (row, col) in black_positions:
                chess_info["棋子颜色"] = "黑色"
                # 找到具体黑色棋子的位置
                index = black_positions.index((row, col))
                chess_info["棋子坐标"] = self.black_rot_coordinates[index]
                chess_info["是否在棋盘上"] = "是"

            # 将当前格子的棋子信息加入总结列表
            summary.append(chess_info)
        return summary

    def chess(self, image):
        # 转换图像为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 使用霍夫圆检测算法检测圆
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=10,
            param1=70,
            param2=30,
            minRadius=20,
            maxRadius=32,
        )

        # 如果检测到圆
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # 遍历每个检测到的圆
            for x, y, r in circles:
                height, width = gray.shape
                offset = 5
                # 确定圆的区域范围
                x_min = max(0, x - offset)
                y_min = max(0, y - offset)
                x_max = min(width, x + offset)
                y_max = min(height, y + offset)

                # 取出圆区域的灰度图像部分
                region = gray[y_min:y_max, x_min:x_max]
                # 计算该区域的平均灰度值
                mean_color = np.mean(region)

                # 如果平均灰度值高于127，认为是白色棋子
                if mean_color > 127:
                    self.white_coordinates.append((x, y, r))
                    # print(
                    #     f"White piece detected at ({x}, {y}), mean color: {mean_color}"
                    # )
                # 否则认为是黑色棋子
                else:
                    self.black_coordinates.append((x, y, r))
                    # print(
                    #     f"Black piece detected at ({x}, {y}), mean color: {mean_color}"
                    # )

    def chess_board(self, image):
        # 将图像转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 检测边缘
        edges = cv2.Canny(gray, 50, 150)
        # 寻找轮廓
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # 设定轮廓面积的最小值和最大值
        min_area = 10000
        max_area = 60000
        # 过滤掉面积不在范围内的轮廓
        filtered_contours = [
            cnt for cnt in contours if min_area < cv2.contourArea(cnt) < max_area
        ]

        if filtered_contours:
            # 找到面积最大的轮廓
            rect = max(filtered_contours, key=cv2.contourArea)
            # 获取最小外接矩形
            rot_rect = cv2.minAreaRect(rect)
            # 获取矩形的四个顶点
            box = cv2.boxPoints(rot_rect)
            box = np.intp(box)

            # 保持点的顺序
            box = self.keep_point_order(box)
            # 定义一些颜色
            colors = [(0, 0, 255), (0, 255, 255), (255, 0, 0), (0, 255, 0)]
            # 在图像上画出矩形的四个顶点
            for i in range(4):
                cv2.circle(image, tuple(box[i]), 5, colors[i], -1)

            # 画出矩形轮廓
            cv2.drawContours(image, [box], 0, (0, 255, 0), 2)

            # 定义棋盘的行和列
            rows = 3
            cols = 3
            # 获取矩形的宽和高
            width = int(rot_rect[1][0])
            height = int(rot_rect[1][1])
            # 计算每个小格子的宽和高
            cell_width = width // cols
            cell_height = height // rows

            # 获取矩形的中心点和旋转角度
            center = tuple(map(int, rot_rect[0]))
            angle = rot_rect[2]
            if angle > 50:
                angle = angle - 90

            # 获取矩形的第一个点和第三个点
            first_point = box[0]
            third_point = box[2]

            x1, y1 = first_point
            x2, y2 = third_point

            # 计算每个小格子的中心点
            self.grid_centers = []
            for i in range(3):
                for j in range(3):
                    center_x = (x1 + (x2 - x1) / 6) + (x2 - x1) / 3 * j
                    center_y = (y1 + (y2 - y1) / 6) + (y2 - y1) / 3 * i
                    self.grid_centers.append((center_x, center_y))

            # 获取旋转矩阵
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            # 旋转图像
            rotated_image = cv2.warpAffine(
                image, rotation_matrix, (image.shape[1], image.shape[0])
            )
            # 获取旋转后的矩形的外接矩形
            x, y, w, h = cv2.boundingRect(
                cv2.transform(np.array([box]), rotation_matrix)
            )
            # 裁剪旋转后的图像
            cropped_image = rotated_image[y : y + h, x : x + w]

            # 处理白棋子坐标
            for coordinate in self.white_coordinates[:]:
                wx, wy = self.coordinates_transformation(
                    rotation_matrix, coordinate[0], coordinate[1]
                )
                wx = wx - x
                wy = wy - y
                if (
                    0 <= int(wx) < cropped_image.shape[1]
                    and 0 <= int(wy) < cropped_image.shape[0]
                ):
                    self.white_coordinates.remove(coordinate)
                    self.white_chess_coordinates.append(coordinate)
                    self.white_rot_coordinates.append((wx, wy, 0))

                    # 在裁剪的图像上画出白棋子
                    cv2.circle(
                        cropped_image,
                        (int(wx), int(wy)),
                        coordinate[2],
                        (255, 255, 255),
                        -1,
                    )

            # 处理黑棋子坐标
            for coordinate in self.black_coordinates[:]:
                wx, wy = self.coordinates_transformation(
                    rotation_matrix, coordinate[0], coordinate[1]
                )
                wx = wx - x
                wy = wy - y
                if (
                    0 <= int(wx) < cropped_image.shape[1]
                    and 0 <= int(wy) < cropped_image.shape[0]
                ):
                    self.black_coordinates.remove(coordinate)
                    self.black_chess_coordinates.append(coordinate)
                    self.black_rot_coordinates.append((wx, wy))

                    # 在裁剪的图像上画出黑棋子
                    cv2.circle(
                        cropped_image, (int(wx), int(wy)), coordinate[2], (0, 0, 0), -1
                    )

            # 检查裁剪区域是否有效
            if x < 0 or y < 0 or w <= 0 or h <= 0:
                # print("Invalid cropping area.")
                cropped_image = np.zeros((1, 1, 3), dtype=np.uint8)  # 创建一个空白图像
            else:
                cropped_image = rotated_image[y : y + h, x : x + w]

            # 画出格子的横线
            for i in range(1, rows):
                cv2.line(
                    cropped_image,
                    (0, i * cell_height),
                    (w, i * cell_height),
                    (255, 0, 0),
                    2,
                )
            # 画出格子的竖线
            for j in range(1, cols):
                cv2.line(
                    cropped_image,
                    (j * cell_width, 0),
                    (j * cell_width, h),
                    (255, 0, 0),
                    2,
                )

            white_positions = []
            black_positions = []

            # 将白棋子的旋转坐标转换为行列坐标
            for id, item in enumerate(self.white_rot_coordinates[:]):
                wx, wy = item[:2]
                row = int(wy // cell_height)
                row = max(0, min(row, 2))
                col = int(wx // cell_width)
                col = max(0, min(col, 2))
                white_positions.append((row, col))
                self.grid[row, col] = 1  # 1 表示白棋
                # x, y, 0~8
                self.white_rot_coordinates[id] = (wx, wy, row * 3 + col)

            # 将黑棋子的旋转坐标转换为行列坐标
            for id, item in enumerate(self.black_rot_coordinates):
                bx, by = item
                row = int(by // cell_height)
                row = max(0, min(row, 2))
                col = int(bx // cell_width)
                col = max(0, min(col, 2))
                black_positions.append((row, col))
                self.grid[row, col] = 2  # 2 表示黑棋
                # x, y, 0~8
                self.black_rot_coordinates[id] = (bx, by, row * 3 + col)

            # 总结棋子信息
            summary = self.summarize_chess_info(
                self.grid_centers, white_positions, black_positions
            )
            for info in summary:
                pass
                # print(
                #     f"格子中心坐标: {info['格子中心坐标']}, 棋子颜色: {info['棋子颜色']}, 棋子坐标: {info['棋子坐标']}, 是否在棋盘上: {info['是否在棋盘上']}"
                # )

            # 画出所有白棋子
            self.draw_circle(image, self.white_chess_coordinates, (0, 255, 0))
            # 画出所有黑棋子
            self.draw_circle(image, self.black_chess_coordinates, (0, 255, 0))
            # 画出未被检测到的白棋子
            self.draw_circle(image, self.white_coordinates, (0, 0, 255))
            # 画出未被检测到的黑棋子
            self.draw_circle(image, self.black_coordinates, (0, 0, 255))

            # 显示检测到的格子图像
            cv2.imshow("Grid", cropped_image)
            # 打印出当前棋盘状态
            # print(self.grid)

        else:
            # print("No chessboard detected.")  # 没有检测到棋盘
            pass

        # 显示旋转后的图像
        cv2.imshow("Rotated Image", image)
        cv2.waitKey(1)  # 等待键盘输入

    def process_frame(self, image):
        # 清空上一次检测的结果
        self.white_coordinates.clear()
        self.black_coordinates.clear()
        self.white_chess_coordinates.clear()
        self.black_chess_coordinates.clear()
        self.white_rot_coordinates.clear()
        self.black_rot_coordinates.clear()
        self.grid.fill(0)  # 清空棋盘状态

        # 处理图像
        self.chess(image)  # 检测棋子
        self.chess_board(image)  # 检测棋盘并绘制结果


if __name__ == "__main__":
    cap = cv2.VideoCapture(2)  # 打开摄像头设备，参数'1'表示使用第一个摄像头设备
    cap.set(cv2.CAP_PROP_EXPOSURE, -5.98)  # 设置摄像头曝光值
    if not cap.isOpened():  # 检查摄像头是否成功打开
        print(
            "Error: Could not open video capture."
        )  # 如果摄像头没有成功打开，打印错误信息
    else:  # 如果摄像头成功打开
        processor = (
            ChessBoardProcessor()
        )  # 创建一个 ChessBoardProcessor 对象，用于处理棋盘图像
        processor.createControllerWindow()  # 创建一个控制窗口，用于选择功能
        while True:  # 进入一个无限循环，用于不断读取摄像头画面
            ret, img = cap.read()  # 从摄像头读取一帧画面
            if not ret:  # 检查是否成功读取到画面
                print(
                    "Error: Could not read frame."
                )  # 如果没有成功读取到画面，打印错误信息
                break  # 退出循环

            image = img.copy()  # 复制读取到的画面，以备后续处理
            processor.process_frame(image)  # 使用ChessBoardProcessor对象处理复制的画面
            print(processor.black_chess_coordinates)
            print(processor.black_coordinates)
            print(processor.white_chess_coordinates)
            print(processor.white_coordinates)

            if cv2.waitKey(1) & 0xFF == ord(
                "q"
            ):  # 检查键盘输入，如果按下'q'键则退出循环
                break  # 退出循环

    cap.release()  # 释放摄像头资源
    cv2.destroyAllWindows()  # 关闭所有 OpenCV 窗口
