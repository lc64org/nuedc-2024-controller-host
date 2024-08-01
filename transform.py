def calculate_transform_params(point1_src, point1_dst, point2_src, point2_dst):
    """计算线性变换和平移参数"""
    # 计算缩放和旋转
    dx_src = point2_src[0] - point1_src[0]
    dy_src = point2_src[1] - point1_src[1]
    dx_dst = point2_dst[0] - point1_dst[0]
    dy_dst = point2_dst[1] - point1_dst[1]

    scale_x = dx_dst / dx_src if dx_src != 0 else 1
    scale_y = dy_dst / dy_src if dy_src != 0 else 1

    # 计算平移
    translate_x = point1_dst[0] - scale_x * point1_src[0]
    translate_y = point1_dst[1] - scale_y * point1_src[1]

    return scale_x, scale_y, translate_x, translate_y


# 使用第1点和第4点来计算参数
robot_point1, camera_point1 = (238, -81), (46, 324)
robot_point2, camera_point2 = (125, 72), (418, 64)

# 计算从机械臂到摄像头的转换参数
scale_x_rc, scale_y_rc, translate_x_rc, translate_y_rc = calculate_transform_params(
    robot_point1, camera_point1, robot_point2, camera_point2
)

# 计算从摄像头到机械臂的转换参数
scale_x_cr, scale_y_cr, translate_x_cr, translate_y_cr = calculate_transform_params(
    camera_point1, robot_point1, camera_point2, robot_point2
)


def robot_to_camera(robot_x, robot_y):
    """将机械臂坐标转换为摄像头坐标"""
    camera_x = round(scale_x_rc * robot_x + translate_x_rc)
    camera_y = round(scale_y_rc * robot_y + translate_y_rc)
    return camera_x, camera_y


def camera_to_robot(camera_x, camera_y):
    """将摄像头坐标转换为机械臂坐标"""
    robot_x = round(scale_x_cr * camera_x + translate_x_cr)
    robot_y = round(scale_y_cr * camera_y + translate_y_cr)
    return robot_x, robot_y


# 测试函数
print("Testing robot_to_camera function:")
test_points = [(115, -80), (115, 72), (242, -84), (245, 92), (195, 5)]
for point in test_points:
    print(f"Robot {point} to Camera: {robot_to_camera(*point)}")

print("\nTesting camera_to_robot function:")
test_points = [(108, 124), (370, 122), (110, 294), (372, 288), (234, 208)]
for point in test_points:
    print(f"Camera {point} to Robot: {camera_to_robot(*point)}")
