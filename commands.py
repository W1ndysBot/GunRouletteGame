# app/scripts/GunRouletteGame/commands.py

import logging
from app.api import send_group_msg
from app.scripts.GunRouletteGame.menu import Menu
from app.scripts.GunRouletteGame.GameManager import (
    GameManager,
    MIN_BET_AMOUNT,
    MAX_BET_AMOUNT,
)
from app.scripts.GunRouletteGame.DataManager import DataManager

DEFAULT_BULLET_COUNT = 6
DEFAULT_BET_AMOUNT = 1  # 默认押注点数


async def handle_my_roulette(websocket, group_id, user_id, message_id):
    """处理我的轮盘命令"""
    data_manager = DataManager(group_id)
    my_roulette = data_manager.get_my_roulette(user_id)
    message = f"[CQ:reply,id={message_id}]"
    message += my_roulette
    try:
        await send_group_msg(websocket, group_id, message)
    except Exception as e:
        logging.error(f"处理我的轮盘命令失败: {e}")


async def handle_roulette_rank(websocket, group_id, message_id):
    """处理轮盘排行榜命令"""
    data_manager = DataManager(group_id)
    rank_list = data_manager.get_rank()
    rank_message = "轮盘排行榜\n"
    rank_message += "-----------------\n"
    for i, rank in enumerate(rank_list, 1):
        rank_message += f"{i}. {rank['user_id']}：{rank['total_score']}分\n"
    try:
        await send_group_msg(websocket, group_id, rank_message)
    except Exception as e:
        logging.error(f"处理轮盘排行榜命令失败: {e}")


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


async def handle_start_roulette_game(
    websocket, group_id, user_id, raw_message, message_id
):
    """处理开始卷卷轮盘游戏命令"""
    bullet_count = DEFAULT_BULLET_COUNT
    command_keyword = "开始轮盘"

    # 从原始消息中提取命令关键字后的参数部分
    # 例如: "开始轮盘", "开始轮盘8", "开始轮盘 8"
    # 移除 "开始轮盘" 前缀，并去除两端可能存在的空格
    parameter_str = raw_message[len(command_keyword):].strip()

    if parameter_str:  # 如果关键字 "开始轮盘" 之后有非空白内容
        try:
            parsed_bullet_count = int(parameter_str)
            if parsed_bullet_count > 0:
                bullet_count = parsed_bullet_count
            else:
                # 子弹数必须为正整数
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]无效的子弹数量，必须为正整数。将使用默认值 {DEFAULT_BULLET_COUNT} 颗。",
                )
                # bullet_count 保持默认值 DEFAULT_BULLET_COUNT
        except ValueError:
            # 参数不是一个有效的整数 (例如 "abc", "8 abc")
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]无效的子弹数量格式，请输入纯数字。将使用默认值 {DEFAULT_BULLET_COUNT} 颗。",
            )
            # bullet_count 保持默认值 DEFAULT_BULLET_COUNT
    # 如果 parameter_str 为空 (即命令仅为 "开始轮盘"), bullet_count 保持默认值 DEFAULT_BULLET_COUNT

    try:
        # 实例化GameManager，传入 initiator_id
        game_manager = GameManager(
            group_id=group_id, initiator_id=user_id, bullet_count=bullet_count
        )
        game_result = game_manager.start_game()

        reply_message = f"[CQ:reply,id={message_id}]"
        if game_result and game_result.get("success"):
            # 游戏开始成功的消息由 GameManager 返回
            await send_group_msg(
                websocket,
                group_id,
                f"{reply_message}{game_result.get('message')}",
            )
        elif game_result:  # game_result 存在但 success 为 False
            await send_group_msg(
                websocket,
                group_id,
                f"{reply_message}🚫🚫🚫开启卷卷轮盘游戏失败，失败原因："
                + game_result.get("message", "未知错误"),
            )
        else:  # game_result 为 None 或其他意外情况
            await send_group_msg(
                websocket,
                group_id,
                f"{reply_message}🚫🚫🚫开启卷卷轮盘游戏失败，无法获取游戏结果。",
            )
    except Exception as e:
        logging.error(f"开始卷卷轮盘游戏失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}] 🚫🚫🚫开启卷卷轮盘游戏失败，发生内部错误: {str(e)}",
        )


async def handle_player_shoot(websocket, group_id, user_id, raw_message, message_id):
    """处理玩家开枪命令"""
    bet_amount = DEFAULT_BET_AMOUNT  # 默认押注1点
    try:
        command_keyword = "开枪"
        # 确保消息以 "开枪" 开头，然后提取后续的参数
        if raw_message.startswith(command_keyword):
            potential_bet_str = raw_message[len(command_keyword) :].strip()

            if potential_bet_str:  # 如果 "开枪" 后面有内容
                try:
                    parsed_bet = int(potential_bet_str)
                    if MIN_BET_AMOUNT <= parsed_bet <= MAX_BET_AMOUNT:
                        bet_amount = parsed_bet
                    else:
                        await send_group_msg(
                            websocket,
                            group_id,
                            f"[CQ:reply,id={message_id}]️️️无效的押注点数，请输入 {MIN_BET_AMOUNT}-{MAX_BET_AMOUNT} 之间的整数，将使用默认值 {DEFAULT_BET_AMOUNT} 点。",
                        )
                        # bet_amount 保持为 DEFAULT_BET_AMOUNT
                except ValueError:
                    await send_group_msg(
                        websocket,
                        group_id,
                        f"[CQ:reply,id={message_id}]️️️无效的押注点数，请输入数字，将使用默认值 {DEFAULT_BET_AMOUNT} 点。",
                    )
                    # bet_amount 保持为 DEFAULT_BET_AMOUNT
            # else: 如果 potential_bet_str 为空，表示玩家只发送了 "开枪"，使用默认押注
        else:
            # 此情况理论上不应发生，因为 main.py 中有 startswith("开枪") 的判断
            # 但为保险起见，记录一个警告，并使用默认押注
            logging.warning(
                f"handle_player_shoot 接收到非预期格式的消息: {raw_message}"
            )
            # bet_amount 保持为 DEFAULT_BET_AMOUNT

    except Exception as e:
        logging.warning(f"解析押注点数时出错: {e}，将使用默认值。")
        # bet_amount 保持默认值

    try:
        # GameManager 需要 group_id 来加载正确的游戏状态，但不需要 initiator_id 和 bullet_count 进行开枪操作
        # 可以在 GameManager 中直接从加载的 game_status 获取 bullet_count
        # 但为了保持一致性或未来可能的扩展，我们可以选择实例化一个新的GameManager对象
        # 或者，如果 GameManager 设计为单例或可重用，则可以直接调用方法
        # 当前设计，每次都实例化一个新的 Manager，它会自己加载状态
        game_manager = GameManager(
            group_id=group_id, initiator_id=user_id
        )  # initiator_id 在 player_shoot 中实际未使用，但构造函数需要
        shoot_result = game_manager.player_shoot(user_id=user_id, bet_amount=bet_amount)

        reply_message_base = f"[CQ:reply,id={message_id}]"

        if shoot_result and shoot_result.get("success"):
            message_to_send = f"{reply_message_base}{shoot_result.get('message')}"
            await send_group_msg(websocket, group_id, message_to_send)

            # 如果游戏结束，可以考虑发送一个更详细的总结，或者已经在 shoot_result['message'] 中
            # if shoot_result.get("game_over"):
            #     details = shoot_result.get("details", {})
            #     summary_message = details.get("summary", "游戏已结束。")
            #     # await send_group_msg(websocket, group_id, f"本场游戏总结：\n{summary_message}")

        elif shoot_result:  # shoot_result 存在但 success 为 False
            await send_group_msg(
                websocket,
                group_id,
                f"{reply_message_base}🚫{shoot_result.get('message', '操作失败')}",
            )
        else:
            await send_group_msg(
                websocket,
                group_id,
                f"{reply_message_base}🚫开枪失败，无法获取游戏结果。",
            )

    except Exception as e:
        logging.error(f"处理玩家开枪命令失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}] 🚫处理开枪命令失败，发生内部错误: {str(e)}。",
        )


async def handle_admin_end_game(websocket, group_id, message_id):
    """处理管理员结束游戏命令"""
    try:
        # GameManager 的 initiator_id 在此场景下不重要，但构造函数需要
        # 可以传入一个占位符或者管理员自己的ID（如果需要记录操作者）
        # 这里我们用一个通用占位符，因为游戏结束逻辑不依赖它
        admin_user_id_placeholder = "admin_action"
        game_manager = GameManager(
            group_id=group_id, initiator_id=admin_user_id_placeholder
        )
        result = game_manager.admin_end_game()

        reply_message_base = f"[CQ:reply,id={message_id}]"

        if result and result.get("success"):
            await send_group_msg(
                websocket,
                group_id,
                f"{reply_message_base}{result.get('message')}",
            )
        elif result:  # result 存在但 success 为 False
            await send_group_msg(
                websocket,
                group_id,
                f"{reply_message_base}🚫{result.get('message', '操作失败')}",
            )
        else:
            await send_group_msg(
                websocket,
                group_id,
                f"{reply_message_base}🚫结束游戏失败，无法获取处理结果。",
            )
    except Exception as e:
        logging.error(f"管理员结束游戏失败: {e}", exc_info=True)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}] 🚫管理员结束游戏时发生内部错误: {str(e)}。",
        )
