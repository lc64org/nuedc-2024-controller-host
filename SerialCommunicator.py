import struct
import time

import serial
import serial.tools.list_ports
import serial.tools.list_ports_common


class SerialCommunicator:
    def __init__(self):
        self.serial = None
        self.last_x, self.last_y, self.last_z = 0, 0, 0

    @staticmethod
    def list_serial_ports():
        """列出可用的串口"""
        ports = serial.tools.list_ports.comports()
        if not ports:
            print("没有可用的串口")
        else:
            print("可用串口：")
            for i, port in enumerate(ports):
                print(f"{i + 1}. {port.device} - {port.description}")
        return ports

    @staticmethod
    def prompt_serial_ports(
        ports: list[serial.tools.list_ports_common.ListPortInfo] | None = None,
    ):
        """在控制台列出可用的串口，并返回用户选择的串口"""
        if ports is None:
            ports = SerialCommunicator.list_serial_ports()
            if not ports:
                return None
        else:
            print("可用串口：")
            for i, port in enumerate(ports):
                print(f"{i + 1}. {port.device} - {port.description}")

        choice = int(input("请输入串口编号：")) - 1
        if 0 <= choice < len(ports):
            return ports[choice].device
        else:
            print("无效的选择")
            return None

    def connect(self, port: str | None = None):
        """连接到串口并返回连接状态，若传入的串口参数为空，则在控制台列出可用的串口并由用户选择"""
        if port is None:
            # 连接到选定的串口
            port = self.prompt_serial_ports()
            if port is None:
                return False

        try:
            self.serial = serial.Serial(port, 250000, timeout=2)
            print(f"已连接到 {port}")

            # 等待设备初始化并接收欢迎消息
            time.sleep(2)
            hello = self.receive_response(timeout=5)
            if hello.startswith("Hello"):
                print("欢迎消息:", hello)
                return True
            else:
                print("未收到正确的欢迎消息")
                return False
        except serial.SerialException as e:
            print(f"串口通信错误: {e}")
            return False

    def disconnect(self):
        """断开串口连接"""
        if self.serial:
            self.serial.close()
            print("串口已关闭")

    def receive_response(self, timeout: float = 1.0):
        """按行阻塞并等待串口响应，返回响应字符串"""
        response = b""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial.in_waiting:
                byte = self.serial.read(1)
                response += byte
                if byte == b"\n":  # 假设每个响应以换行符结束
                    break
        return response.decode("utf-8", errors="ignore").strip()

    @staticmethod
    def calculate_packet(
        valid_op: bool,
        system_on: bool,
        pump_on: bool,
        motor_on: bool,
        x: float,
        y: float,
        z: float,
    ):
        """计算并返回数据包"""
        first_byte = 0
        if valid_op:
            first_byte |= 0x80
        if system_on:
            first_byte |= 0x40
        if pump_on:
            first_byte |= 0x20
        if motor_on:
            first_byte |= 0x10

        first_byte |= first_byte >> 4

        x_bytes = struct.pack("f", x)
        y_bytes = struct.pack("f", y)
        z_bytes = struct.pack("f", z)

        data = bytearray([first_byte]) + x_bytes + y_bytes + z_bytes

        checksum = 0
        for byte in data:
            checksum ^= byte

        data.append(checksum)
        return data

    def send_command(
        self,
        valid_op: bool,
        system_on: bool,
        pump_on: bool,
        motor_on: bool,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        deltaX: bool = False,
        deltaY: bool = False,
        deltaZ: bool = False,
    ):
        """尝试发送命令并接收响应"""
        # 发送命令并接收响应
        if not valid_op:
            packet = self.calculate_packet(False, False, False, False, 0, 0, 0)
        elif not system_on:
            packet = self.calculate_packet(True, False, False, False, 0, 0, 0)
        else:
            if motor_on:
                if deltaX:
                    self.last_x += x
                else:
                    self.last_x = x

                if self.last_x <= 0:
                    self.last_x, self.last_y, self.last_z = 0, 0, 0
                else:
                    if deltaY:
                        self.last_y += y
                    else:
                        self.last_y = y

                    if deltaZ:
                        self.last_z += z
                    else:
                        self.last_z = z

            else:
                self.last_x, self.last_y, self.last_z = 0, 0, 0

            packet = self.calculate_packet(
                True, True, pump_on, motor_on, self.last_x, self.last_y, self.last_z
            )

        print("\n发送数据包:", packet.hex())

        try:
            self.serial.write(packet)
        except serial.SerialException as e:
            print(f"串口通信错误: {e}")
            return None, None

        print("等待第一个响应...")
        first_response = self.receive_response()
        if first_response:
            print("收到第一个响应:", first_response)
        else:
            print("未收到第一个响应")

        print("等待第二个响应...")
        second_response = self.receive_response(timeout=30)
        if second_response:
            print("收到第二个响应:", second_response)
        else:
            print("未收到第二个响应")

        return first_response, second_response


def main():
    communicator = SerialCommunicator()
    result = communicator.connect()
    if not result:
        return

    try:
        while True:
            # 发送数据
            valid_op = input("Valid operation? (*1/0) ").lower() != "0"
            if not valid_op:
                packet = communicator.send_command(False, False, False, False)
            else:
                system_on = input("System on? (*1/0) ").lower() != "0"
                if not system_on:
                    packet = communicator.send_command(True, False, False, False)
                else:
                    pump_on = input("Pump on? (1/0*) ").lower() == "1"
                    motor_on = input("Motor on? (1/0*) ").lower() == "1"

                    deltaX, deltaY, deltaZ = False, False, False

                    if motor_on:  # 检查电机是否开启
                        xStr = input("X: ")  # 提示用户输入X坐标值
                        if xStr.startswith("d"):  # 检查输入是否以'd'开头，表示增量改变
                            deltaX = True
                            xStr = xStr[1:]
                        x = float(xStr)  # 否则，将输入值直接转换为浮点数赋值给X
                        if x > 0:  # 检查X坐标是否为正值
                            yStr = input("Y: ")  # 提示用户输入Y坐标值
                            if yStr.startswith(
                                "d"
                            ):  # 检查输入是否以'd'开头，表示增量改变
                                deltaY = True
                                yStr = yStr[1:]
                            y = float(yStr)  # 否则，将输入值直接转换为浮点数赋值给Y

                            zStr = input("Z: ")  # 提示用户输入Z坐标值
                            if zStr.startswith(
                                "d"
                            ):  # 检查输入是否以'd'开头，表示增量改变
                                deltaZ = True
                                zStr = zStr[1:]
                            z = float(zStr)

                        else:
                            x, y, z = (
                                0,
                                0,
                                0,
                            )  # 若X为负，则恢复到之前的 X, Y 和 Z 值
                    else:
                        x, y, z = 0, 0, 0  # 若电机未开启，则将X, Y和Z都设为 0

                    packet = communicator.send_command(
                        True, True, pump_on, motor_on, x, y, z, deltaX, deltaY, deltaZ
                    )

            print("\n")

    except serial.SerialException as e:
        print(f"串口通信错误: {e}")
    finally:
        communicator.disconnect()


if __name__ == "__main__":
    main()
