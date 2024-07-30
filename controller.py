import struct
import time

import serial
import serial.tools.list_ports


def calculate_packet(valid_op, system_on, pump_on, motor_on, x, y, z):
    # 构建第一个字节
    first_byte = 0
    if valid_op:
        first_byte |= 0x80
    if system_on:
        first_byte |= 0x40
    if pump_on:
        first_byte |= 0x20
    if motor_on:
        first_byte |= 0x10

    # 添加校验位
    first_byte |= first_byte >> 4

    # 将 float 值打包成字节
    x_bytes = struct.pack("f", x)
    y_bytes = struct.pack("f", y)
    z_bytes = struct.pack("f", z)

    # 组合所有数据
    data = bytearray([first_byte]) + x_bytes + y_bytes + z_bytes

    # 计算校验和
    checksum = 0
    for byte in data:
        checksum ^= byte

    # 添加校验和到数据末尾
    data.append(checksum)

    return data


def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("没有可用的串口")
        return None

    print("可用串口:")
    for i, port in enumerate(ports):
        print(f"{i + 1}. {port.device} - {port.description}")

    choice = int(input("请选择串口 (输入编号): ")) - 1
    if 0 <= choice < len(ports):
        return ports[choice].device
    else:
        print("无效的选择")
        return None


def receive_response(ser, timeout=1):
    response = b""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if ser.in_waiting:
            byte = ser.read(1)
            response += byte
            if byte == b"\n":  # 假设每个响应以换行符结束
                break
    return response.decode("utf-8", errors="ignore").strip()


def serial_communication():
    port = list_serial_ports()
    if not port:
        return

    try:
        ser = serial.Serial(port, 250000, timeout=1)
        print(f"已连接到 {port}")

        while True:
            time.sleep(2)  # 等待设备初始化

            hello = receive_response(ser)  # 接收欢迎消息

            if hello.startswith("Hello"):
                print("欢迎消息:", hello)
                break

        last_x, last_y, last_z = 0, 0, 0

        while True:
            # 发送数据
            valid_op = input("Valid operation? (*1/0) ").lower() != "0"
            if not valid_op:
                packet = calculate_packet(False, False, False, False, 0, 0, 0)
            else:
                system_on = input("System on? (*1/0) ").lower() != "0"
                if not system_on:
                    packet = calculate_packet(True, False, False, False, 0, 0, 0)
                else:
                    pump_on = input("Pump on? (1/0*) ").lower() == "1"
                    motor_on = input("Motor on? (1/0*) ").lower() == "1"

                    if motor_on:  # 检查电机是否开启
                        xStr = input("X: ")  # 提示用户输入X坐标值
                        if xStr.startswith("d"):  # 检查输入是否以'd'开头，表示增量改变
                            x += float(xStr[1:])  # 将增量值加到当前的X坐标上
                        else:
                            x = float(xStr)  # 否则，将输入值直接转换为浮点数赋值给X
                        if x >= 0:  # 检查X坐标是否为非负值
                            yStr = input("Y: ")  # 提示用户输入Y坐标值
                            if yStr.startswith(
                                "d"
                            ):  # 检查输入是否以'd'开头，表示增量改变
                                y += float(yStr[1:])  # 将增量值加到当前的Y坐标上
                            else:
                                y = float(yStr)  # 否则，将输入值直接转换为浮点数赋值给Y

                            zStr = input("Z: ")  # 提示用户输入Z坐标值
                            if zStr.startswith(
                                "d"
                            ):  # 检查输入是否以'd'开头，表示增量改变
                                z += float(zStr[1:])  # 将增量值加到当前的Z坐标上
                            else:
                                z = float(
                                    zStr
                                )  # 否则，将输入值直接转换为浮点数赋值给 Z
                        else:
                            x, y, z = (
                                last_x,
                                last_y,
                                last_z,
                            )  # 若X为负，则恢复到之前的 X, Y 和 Z 值
                    else:
                        x, y, z = 0, 0, 0  # 若电机未开启，则将X, Y和Z都设为0

                    last_x, last_y, last_z = x, y, z
                    packet = calculate_packet(True, True, pump_on, motor_on, x, y, z)

            print("\nSending packet:", packet.hex())
            ser.write(packet)

            # 接收第一个响应
            print("Waiting for first response...")
            first_response = receive_response(ser, 20)
            if first_response:
                print("First response received:", first_response)
            else:
                print("No first response received")

            # 接收第二个响应
            print("Waiting for second response...")
            second_response = receive_response(ser)
            if second_response:
                print("Second response received:", second_response)
            else:
                print("No second response received")

            print("\n")

    except serial.SerialException as e:
        print(f"串口通信错误: {e}")
    finally:
        if "ser" in locals():
            ser.close()
            print("串口已关闭")


if __name__ == "__main__":
    serial_communication()
