# script/GunRouletteGame/main.py

import logging
import os
import sys
import re
import json

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import *
from app.api import send_group_msg, send_private_msg, owner_id
from app.switch import load_switch, save_switch
from app.scripts.GunRouletteGame.menu import Menu
from app.scripts.GunRouletteGame.GameManager import GameManager
from app.scripts.GunRouletteGame.commands import (
    handle_roulette_menu,
    handle_start_roulette_game,
    handle_player_shoot,
    handle_admin_end_game,
)

# 数据存储路径，实际开发时，请将GunRouletteGame替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "GunRouletteGame",
)


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "GunRouletteGame")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "GunRouletteGame", status)


# 处理开关状态
async def toggle_function_status(websocket, group_id, message_id, authorized_user_flag):
    """切换指定群组的功能开关状态"""
    if not authorized_user_flag:  # 使用传入的标志
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]抱歉，您没有权限操作 GunRouletteGame 功能开关。",
        )
        return

    current_status = load_function_status(group_id)
    new_status = not current_status
    save_function_status(group_id, new_status)
    status_text = "开启" if new_status else "关闭"
    await send_group_msg(
        websocket,
        group_id,
        f"[CQ:reply,id={message_id}]枪轮盘游戏功能已{status_text}。",
    )


# 群消息处理函数
async def handle_group_message(websocket, msg):
    """处理群消息"""
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message", "")).strip()
        message_id = str(msg.get("message_id"))
        role = str(msg.get("sender", {}).get("role", ""))
        is_authorized_user = user_id in owner_id or role in ["admin", "owner"]

        # 处理开关命令 (grg)
        if raw_message.lower() == "grg":
            # toggle_function_status 内部已经有权限判断，但这里提前判断也可以
            # 为了统一，toggle_function_status 也应该接收 is_authorized_user
            await toggle_function_status(
                websocket, group_id, message_id, is_authorized_user
            )
            return

        # 检查功能是否开启
        if not load_function_status(group_id):
            return

        # 功能已开启，处理游戏相关命令
        if raw_message.lower() == "轮盘菜单":
            await handle_roulette_menu(websocket, group_id, message_id)
            return

        if raw_message.startswith("开始轮盘"):
            await handle_start_roulette_game(
                websocket, group_id, user_id, raw_message, message_id
            )
            return

        if raw_message.startswith("开枪"):
            await handle_player_shoot(
                websocket, group_id, user_id, raw_message, message_id
            )
            return

        # 新增：处理管理员结束游戏命令
        if raw_message.lower() == "结束轮盘":
            if is_authorized_user:
                await handle_admin_end_game(websocket, group_id, message_id)
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]抱歉，您没有权限结束当前轮盘游戏。",
                )
            return

    except Exception as e:
        logging.error(f"处理GunRouletteGame群消息失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理GunRouletteGame群消息失败，错误信息：" + str(e),
        )
        return


# 私聊消息处理函数
async def handle_private_message(websocket, msg):
    """处理私聊消息"""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        raw_message = str(msg.get("raw_message"))
        # 私聊消息处理逻辑
        pass
    except Exception as e:
        logging.error(f"处理GunRouletteGame私聊消息失败: {e}")
        await send_private_msg(
            websocket,
            msg.get("user_id"),
            "处理GunRouletteGame私聊消息失败，错误信息：" + str(e),
        )
        return


# 群通知处理函数
async def handle_group_notice(websocket, msg):
    """处理群通知"""
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        notice_type = str(msg.get("notice_type"))
        operator_id = str(msg.get("operator_id", ""))

    except Exception as e:
        logging.error(f"处理GunRouletteGame群通知失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理GunRouletteGame群通知失败，错误信息：" + str(e),
        )
        return


# 回应事件处理函数
async def handle_response(websocket, msg):
    """处理回调事件"""
    try:
        echo = msg.get("echo")
        if echo and echo.startswith("xxx"):
            # 回调处理逻辑
            pass
    except Exception as e:
        logging.error(f"处理GunRouletteGame回调事件失败: {e}")
        await send_group_msg(
            websocket,
            msg.get("group_id"),
            f"处理GunRouletteGame回调事件失败，错误信息：{str(e)}",
        )
        return


# 请求事件处理函数
async def handle_request_event(websocket, msg):
    """处理请求事件"""
    try:
        request_type = msg.get("request_type")
        pass
    except Exception as e:
        logging.error(f"处理GunRouletteGame请求事件失败: {e}")
        return


# 统一事件处理入口
async def handle_events(websocket, msg):
    """统一事件处理入口"""
    post_type = msg.get("post_type", "response")  # 添加默认值
    try:
        # 这里可以放一些定时任务，在函数内设置时间差检测即可

        # 处理回调事件，用于一些需要获取ws返回内容的事件
        if msg.get("status") == "ok":
            await handle_response(websocket, msg)
            return

        post_type = msg.get("post_type")

        # 处理元事件，每次心跳时触发，用于一些定时任务
        if post_type == "meta_event":
            pass

        # 处理消息事件，用于处理群消息和私聊消息
        elif post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await handle_group_message(websocket, msg)
            elif message_type == "private":
                await handle_private_message(websocket, msg)

        # 处理通知事件，用于处理群通知
        elif post_type == "notice":
            await handle_group_notice(websocket, msg)

        # 处理请求事件，用于处理请求事件
        elif post_type == "request":
            await handle_request_event(websocket, msg)

    except Exception as e:
        error_type = {
            "message": "消息",
            "notice": "通知",
            "request": "请求",
            "meta_event": "元事件",
        }.get(post_type, "未知")

        logging.error(f"处理GunRouletteGame{error_type}事件失败: {e}")

        # 发送错误提示
        if post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await send_group_msg(
                    websocket,
                    msg.get("group_id"),
                    f"处理GunRouletteGame{error_type}事件失败，错误信息：{str(e)}",
                )
            elif message_type == "private":
                await send_private_msg(
                    websocket,
                    msg.get("user_id"),
                    f"处理GunRouletteGame{error_type}事件失败，错误信息：{str(e)}",
                )
