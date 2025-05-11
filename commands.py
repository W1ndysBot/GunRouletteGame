# app/scripts/GunRouletteGame/commands.py

import logging
from app.api import send_group_msg
from app.scripts.GunRouletteGame.menu import Menu
from app.scripts.GunRouletteGame.GameManager import GameManager

DEFAULT_BULLET_COUNT = 6


async def handle_roulette_menu(websocket, group_id, message_id):
    """处理轮盘菜单命令"""
    try:
        await send_group_msg(websocket, group_id, Menu().get_menu())
    except Exception as e:
        logging.error(f"处理轮盘菜单命令失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}] 获取轮盘菜单失败，错误信息：{str(e)}",
        )


async def handle_start_roulette_game(websocket, group_id, raw_message, message_id):
    """处理开始卷卷轮盘游戏命令"""
    bullet_count = DEFAULT_BULLET_COUNT
    try:
        parts = raw_message.split(" ")
        if len(parts) > 1 and parts[1]:
            try:
                bullet_count = int(parts[1])
            except ValueError:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]️️️无效的子弹数量，将使用默认值{DEFAULT_BULLET_COUNT}颗。",
                )
                # bullet_count 保持默认值
    except Exception as e:  # pylint: disable=broad-except
        logging.warning(f"解析子弹数量时出错: {e}，将使用默认值。")
        # bullet_count 保持默认值

    try:
        # 实例化GameManager
        game_manager = GameManager(group_id, bullet_count)
        game_result = game_manager.start_game()

        if game_result and game_result.get("success") == True:
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]🔫🔫🔫卷卷轮盘游戏已开始，当前子弹数量为{bullet_count}颗，可以发送`卷卷开枪`命令参与游戏。",
            )
        elif game_result:
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]🚫🚫🚫开启卷卷轮盘游戏失败，失败原因："
                + game_result.get("message", "未知错误"),
            )
        else:
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]🚫🚫🚫开启卷卷轮盘游戏失败，无法获取游戏结果。",
            )
    except Exception as e:
        logging.error(f"开始卷卷轮盘游戏失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}] 🚫🚫🚫开启卷卷轮盘游戏失败，发生内部错误。",
        )
