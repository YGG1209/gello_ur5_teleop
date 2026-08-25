"""Robotiq 2F-85 夹爪控制模块。

统一接口（换夹爪时只需替换本文件实现，保持函数签名不变）:
    connect()           → 创建并连接夹爪
    move(g, ratio)      → ratio: 0.0=张开, 1.0=闭合
    open(g) / close(g)  → 快捷开合
    position(g)         → 当前位置 0~255
    disconnect(g)       → 断开连接
"""

import pyrobotiqgripper as rq

COM_PORT = "/dev/ttyUSB1"
BAUDRATE = 115200
DEVICE_ID = 9


def connect():
    """创建并连接夹爪，自动 activate + start。"""
    g = rq.RobotiqGripper(
        com_port=COM_PORT, device_id=DEVICE_ID,
        connection_type=rq.GRIPPER_MODE_RTU, baudrate=BAUDRATE,
    )
    if not g.isActivated():
        g.activate()
    g.start()
    return g


def move(g, ratio, speed=255, force=70):
    """按归一化比例移动。ratio: 0.0=张开, 1.0=闭合。
    自动处理通信超时导致的 NotStarted（moveJ 等长操作后首次调用时触发）。"""
    pos = int(max(0.0, min(1.0, ratio)) * 255)
    try:
        g.move(pos, speed=speed, force=force, wait=False, readStatus=False)
    except rq.GripperNotStartedError:
        g.start()
        g.move(pos, speed=speed, force=force, wait=False, readStatus=False)


def open(g):
    g.open()


def close(g):
    g.close()


def position(g):
    return g.position()


def disconnect(g):
    g.stop()
    g.disconnect()
