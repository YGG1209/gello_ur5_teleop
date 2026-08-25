import numpy as np
import time
import sys, select
import atexit
import gripper_control
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface 
from gello.agents.gello_agent import DynamixelRobotConfig

# 配置 GELLO 硬件参数：舵机ID、初始偏移量、旋转方向及夹爪参数
config = DynamixelRobotConfig(
    joint_ids=(1, 2, 3, 4, 5, 6),
    joint_offsets=(
        5 * np.pi / 4,              # J1: 3.142 (2 * np.pi / 2)
        3 * np.pi / 2,      # J2: 4.712 (3 * np.pi / 2)
        np.pi,              # J3: 3.142 (2 * np.pi / 2)
        np.pi,              # J4: 3.142 (2 * np.pi / 2)
        0,                  # J5: 0.000 (0 * np.pi / 2)
        3 * np.pi / 2,      # J6: 4.712 (3 * np.pi / 2)
    ),
    joint_signs=(1, 1, -1, 1, 1, 1),
    gripper_config=(7, 20, -22),
)

# 初始化 UR 机器人通信接口 (RTDE)
UR_IP = "192.168.100.2"
ur_control = RTDEControlInterface(UR_IP)
ur_receive = RTDEReceiveInterface(UR_IP)

# 初始化 GELLO 控制手柄（连接到指定串口）
gello = config.make_robot(port="/dev/ttyUSB0")

# 定义每个关节的安全限位（弧度）
joint_limit_min = np.array([-6.283, -6.283, -3.14, -6.283, -6.283, -6.283])
joint_limit_max = np.array([ 6.283,  6.283,  3.14,  6.283,  6.283,  6.283])

# 初始同步运动的速度和加速度
INIT_SPEED = 0.25  # rad/s
INIT_ACCEL = 0.1   # rad/s^2

# 获取 GELLO 当前关节角度并应用限位保护
initial_gello_q = np.array(gello.get_joint_state()[:6], dtype=float)
initial_gello_q = np.clip(initial_gello_q, joint_limit_min, joint_limit_max)

print(f"Gello 初始位置: {[f'{q:.2f}' for q in initial_gello_q]}")
# 开始进行夹爪标定
print("夹爪标定 — 反复捏合张开，完成后按回车")
gripper_min = float('inf')
gripper_max = float('-inf')
while True:
    raw_rad = gello._driver.get_joints()[6]
    deg = np.rad2deg(raw_rad)
    gripper_min = min(gripper_min, deg)
    gripper_max = max(gripper_max, deg)
    print(f"\r当前: {deg:.1f}°  |  min: {gripper_min:.1f}°  |  max: {gripper_max:.1f}°", end='')
    if select.select([sys.stdin], [], [], 0.05)[0]:
        input()   # 吃掉回车
        break
print(f"\n标定完成: min={gripper_min:.3f}, max={gripper_max:.3f}")

# 连接夹爪（模块化调用，换夹爪只需改 gripper_control.py）
gripper = gripper_control.connect()
atexit.register(lambda: gripper_control.disconnect(gripper))

# 使 UR 机器人移动到与 GELLO 相同的起始姿态，确保同步
ur_control.moveJ(initial_gello_q.tolist(), INIT_SPEED, INIT_ACCEL)

print("开始遥操")
time.sleep(1) 

# 遥操作参数设置
dt = 0.02                   # 控制周期 (50Hz)
MAX_SPEED = 1.5              # 最大允许速度
MAX_ACCEL = 0.5              # 最大允许加速度
lookahead_time = 0.04        # servoJ 前瞻时间（平滑轨迹）
gain = 300                   # servoJ 比例增益

previous = initial_gello_q   # 记录上一次的指令位置
prev_gripper_cmd = 0          # 上一次夹爪指令（死区用）

# 实时控制主循环
while True:
    loop_start_time = time.time()

    # 获取 GELLO 当前状态并应用限位
    target = np.array(gello.get_joint_state()[:6], dtype=float)
    target = np.clip(target, joint_limit_min, joint_limit_max)

    # 限制机械臂在单位步长允许的最大位移，防止机械臂在单位步长产生巨大跳变
    delta = target - previous
    max_delta = MAX_SPEED * dt
    delta = np.clip(delta, -max_delta, max_delta)

    # 防止细微抖动
    accel = delta / dt
    accel = np.clip(accel, -MAX_ACCEL, MAX_ACCEL)
    delta_accel = accel * dt
    
    # 更新最终控制指令位置
    filtered = previous + delta_accel
    previous = filtered

    # 向 UR 机器人发送伺服运动指令
    ur_control.servoJ(filtered.tolist(), 0, 0, dt, lookahead_time, gain)
    
    # 夹爪映射: GELLO 角度 -> 归一化 0=张开 1=闭合 -> gripper_control
    raw_deg = np.rad2deg(gello._driver.get_joints()[6])
    ratio = (gripper_max - raw_deg) / (gripper_max - gripper_min)
    ratio = max(0.0, min(1.0, ratio))
    cmd = int(ratio * 255)
    if abs(cmd - prev_gripper_cmd) >= 2:
        gripper_control.move(gripper, ratio)
        prev_gripper_cmd = cmd

    # 频率控制：确保循环周期恒定为 dt
    elapsed_time = time.time() - loop_start_time
    if elapsed_time < dt:
        time.sleep(dt - elapsed_time)
        