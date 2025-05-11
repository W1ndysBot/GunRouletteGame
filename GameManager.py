"""
游戏管理类

负责管理每场游戏的相关数据，包括游戏状态、玩家、分数等。
"""

import uuid
import random
from datetime import datetime, timedelta, timezone
from app.scripts.GunRouletteGame.DataManager import DataManager

# 游戏规则常量
# 每日游戏上限
MAX_DAILY_GAMES = 500000
# 玩家发起游戏频率冷却时间（小时）
PLAYER_INITIATION_COOLDOWN_HOURS = 0
# 最小押注点数
MIN_BET_AMOUNT = 1
# 最大押注点数
MAX_BET_AMOUNT = 5
# 默认子弹数
DEFAULT_BULLET_COUNT = 4


class GameManager:
    """
    游戏核心逻辑管理类。

    负责处理游戏的开始、玩家开枪、游戏结束、计分等。
    """

    def __init__(
        self, group_id: str, initiator_id: str, bullet_count: int = DEFAULT_BULLET_COUNT
    ):
        """
        初始化 GameManager。

        Args:
            group_id (str): 群组ID。
            initiator_id (str): 游戏发起者ID。
            bullet_count (int): 轮盘的总子弹数量 (即子弹数)。
        """
        self.group_id = str(group_id)
        self.initiator_id = str(initiator_id)
        self.bullet_count = max(1, int(bullet_count))  # 确保子弹数至少为1
        self.data_manager = DataManager(group_id=self.group_id)

    def start_game(self):
        """
        开始一场新的轮盘游戏。

        进行各种前置检查，如果通过，则初始化游戏数据并保存。

        Returns:
            dict: 包含操作结果和信息的字典。
                  成功: {"success": True, "message": "游戏已开始...", "game_id": ..., "bullet_count": ...}
                  失败: {"success": False, "message": "错误信息..."}
        """
        # 1. 检查当前群组是否已有游戏正在进行
        if self.data_manager.game_status.get("current_game") is not None:
            return {"success": False, "message": "当前群组已有一场轮盘游戏正在进行中。"}

        # 2. 检查群组每日游戏上限
        today_str = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
        if self.data_manager.game_status.get("last_game_end_date") != today_str:
            self.data_manager.game_status["daily_games_ended_count"] = 0
            self.data_manager.game_status["last_game_end_date"] = today_str

        if (
            self.data_manager.game_status.get("daily_games_ended_count", 0)
            >= MAX_DAILY_GAMES
        ):
            return {
                "success": False,
                "message": f"本群今日轮盘游戏已达上限（{MAX_DAILY_GAMES}场）。",
            }

        # 3. 检查玩家发起游戏频率
        player_data = self.data_manager.get_player_data(self.initiator_id)
        now = datetime.now(timezone.utc)
        cooldown_limit_time = now - timedelta(hours=PLAYER_INITIATION_COOLDOWN_HOURS)

        recent_initiations = [
            t
            for t in player_data.get("games_initiated_timestamps", [])
            if datetime.fromisoformat(t) > cooldown_limit_time
        ]
        if recent_initiations:
            # 计算最近一次发起游戏到现在的时间差，用于友好提示
            last_init_time = datetime.fromisoformat(recent_initiations[-1])
            time_since_last_init = now - last_init_time
            remaining_cooldown = (
                timedelta(hours=PLAYER_INITIATION_COOLDOWN_HOURS) - time_since_last_init
            )

            # 将 remaining_cooldown 转换为更易读的格式，例如 xx分xx秒
            remaining_minutes = int(remaining_cooldown.total_seconds() // 60)
            remaining_seconds = int(remaining_cooldown.total_seconds() % 60)

            return {
                "success": False,
                "message": f"您发起游戏过于频繁，请在 {remaining_minutes}分{remaining_seconds}秒 后再试。",
            }
        player_data["games_initiated_timestamps"] = [
            t
            for t in player_data.get("games_initiated_timestamps", [])
            if datetime.fromisoformat(t) > (now - timedelta(days=1))
        ]  # 清理一天前的记录

        # 所有检查通过，开始新游戏
        game_id = uuid.uuid4().hex
        # fatal_bullet_position = random.randint(0, self.bullet_count - 1) # 不再需要固定致命子弹

        current_game_data = {
            "id": game_id,
            "status": "running",  # 游戏状态: "running", "ended"
            "start_time": now.isoformat(),
            "initiator_id": self.initiator_id,
            "bullet_count": self.bullet_count,  # 总弹巢数
            # "fatal_bullet_position": fatal_bullet_position,  # 移除
            "real_bullet_initially_present": True,  # 默认游戏开始时有一颗子弹
            "is_bullet_fired_this_game": False,  # 标记子弹是否已被击发
            "shots_fired_count": 0,  # 已开枪次数
            "participants": {},  # {user_id: {"bet": int, "shot_order": int, "is_hit": bool, "shot_time": "iso_timestamp"}}
        }

        self.data_manager.game_status["current_game"] = current_game_data
        self.data_manager.save_game_status()

        # 记录玩家发起游戏的时间戳
        self.data_manager.record_player_game_initiation(self.initiator_id)

        return {
            "success": True,
            "message": f"🔫🔫🔫 卷卷轮盘游戏已开始！\n总共 {self.bullet_count} 个弹膛，膛内装有一颗子弹。每次开枪都会重新旋转！\n发送 `开枪 押注点数` (1-{MAX_BET_AMOUNT}点) 来参与游戏！",
            "game_id": game_id,
            "bullet_count": self.bullet_count,
        }

    def player_shoot(self, user_id: str, bet_amount: int):
        """
        处理玩家开枪的逻辑。

        Args:
            user_id (str): 开枪的玩家ID。
            bet_amount (int): 玩家的押注点数。

        Returns:
            dict: 包含操作结果和信息的字典。
                  例如: {"success": True, "message": "...", "game_over": False/True, "hit": False/True}
                  失败: {"success": False, "message": "错误信息..."}
        """
        game_data = self.data_manager.game_status.get("current_game")

        # 1. 检查游戏状态
        if not game_data or game_data.get("status") != "running":
            return {"success": False, "message": "当前没有正在进行的轮盘游戏。"}

        # 2. 检查玩家是否已开枪
        if user_id in game_data["participants"]:
            return {"success": False, "message": "您已经开过枪了，请等待本轮游戏结束。"}

        # 3. 验证押注点数
        try:
            bet_amount = int(bet_amount)
            if not (MIN_BET_AMOUNT <= bet_amount <= MAX_BET_AMOUNT):
                return {
                    "success": False,
                    "message": f"无效的押注点数，请输入 {MIN_BET_AMOUNT} 到 {MAX_BET_AMOUNT} 之间的整数。",
                }
        except ValueError:
            return {"success": False, "message": "无效的押注点数，请输入一个整数。"}

        # 4. 记录玩家参与信息
        shot_order = game_data["shots_fired_count"]  # 从0开始计数
        game_data["participants"][user_id] = {
            "bet": bet_amount,
            "shot_order": shot_order,
            "is_hit": False,  # 默认为未命中
            "shot_time": datetime.now(timezone.utc).isoformat(),
        }

        # 5. 判断是否命中
        is_hit = False
        if game_data.get("real_bullet_initially_present") and not game_data.get(
            "is_bullet_fired_this_game"
        ):
            # 只有在初始有子弹且子弹本局未被击发时，才有概率命中
            if game_data["bullet_count"] > 0:  # 避免除以零
                hit_probability = 1.0 / game_data["bullet_count"]
                if random.random() < hit_probability:
                    is_hit = True
                    game_data["is_bullet_fired_this_game"] = True  # 标记子弹已被击发

        if is_hit:
            game_data["participants"][user_id]["is_hit"] = True

        game_data["shots_fired_count"] += 1  # 无论是否命中，都增加已开枪次数
        self.data_manager.save_game_status()  # 保存参与者、开枪次数和子弹击发状态的更新

        if is_hit:
            # 玩家中弹，游戏结束
            end_game_result = self._end_game(hit_player_id=user_id)
            return {
                "success": True,
                "message": f"💥 BOOM! 玩家 {user_id} (押注 {bet_amount} 点) 不幸中弹！💀\n{end_game_result['summary']}",
                "game_over": True,
                "hit": True,
                "details": end_game_result,
            }
        else:
            # 未中弹
            # 检查是否所有子弹都已安全射出 (即所有膛都打完了)
            if game_data["shots_fired_count"] == game_data["bullet_count"]:
                # 所有子弹打完，无人中弹
                end_game_result = self._end_game(hit_player_id=None)
                
                # 根据子弹是否真的存在过来定制消息
                if game_data.get("real_bullet_initially_present") and not game_data.get("is_bullet_fired_this_game"):
                    # 有子弹，但幸运躲过
                    safe_message = f"🎉 幸运至极！膛内的子弹躲过了所有 {game_data['bullet_count']} 次射击！"
                elif not game_data.get("real_bullet_initially_present"):
                    # 开始就没子弹
                    safe_message = f"🎉 原来如此！所有 {game_data['bullet_count']} 个弹膛原本就是安全的！"
                else: # 理论上这个分支不会到，因为如果 is_bullet_fired_this_game 是 True, is_hit 就该是 True
                    safe_message = f"🎉 咔！是空枪！所有 {game_data['bullet_count']} 个弹膛均已安全射出！"

                return {
                    "success": True,
                    "message": f"{safe_message} 玩家 {user_id} (押注 {bet_amount} 点) 安全。\n{end_game_result['summary']}",
                    "game_over": True,
                    "hit": False,
                    "details": end_game_result,
                }
            else:
                remaining_shots_display = (
                    game_data["bullet_count"] - game_data["shots_fired_count"]
                )
                # 计算下一枪的中弹概率 (如果子弹还未被击发)
                next_shot_probability_display = 0.0
                if game_data.get("real_bullet_initially_present") and not game_data.get("is_bullet_fired_this_game"):
                    if game_data["bullet_count"] > 0:
                        next_shot_probability_display = (1.0 / game_data["bullet_count"]) * 100
                
                probability_message = ""
                if game_data.get("real_bullet_initially_present"):
                    if not game_data.get("is_bullet_fired_this_game"):
                        probability_message = f"\n下一枪中弹概率（如果子弹还在）：{next_shot_probability_display:.1f}%"
                    else:
                        probability_message = "\n子弹已被击发，后续将是安全的！"
                else:
                    probability_message = "\n膛内无子弹，尽情射击吧！"


                return {
                    "success": True,
                    "message": f"咔！是空枪！玩家 {user_id} (押注 {bet_amount} 点) 安全。\n还有 {remaining_shots_display} 次射击机会。本轮盘总共 {game_data['bullet_count']} 个弹膛。{probability_message}",
                    "game_over": False,
                    "hit": False,
                }

    def _end_game(self, hit_player_id: str | None = None):  # 修正类型提示
        """
        结束当前游戏，计算得分，保存历史记录。
        此方法由 player_shoot 内部调用。

        Args:
            hit_player_id (str | None, optional): 中弹玩家的ID。如果为None，则表示无人中弹。

        Returns:
            dict: 包含游戏结算信息的字典。
                  { "game_id": ..., "summary": "结算摘要...", "scores": {user_id: score_change}, "outcome": ... }
        """
        game_data = self.data_manager.game_status.get("current_game")
        if not game_data:  # 理论上不应发生，因为调用此函数前游戏应存在
            return {"summary": "错误：未找到当前游戏数据进行结算。"}

        now_iso = datetime.now(timezone(timedelta(hours=8))).isoformat()
        game_id = game_data["id"]
        bullet_count = game_data["bullet_count"]
        participants = game_data["participants"]

        score_changes = {}
        outcome_summary_parts = ["本场轮盘结算："]

        if hit_player_id:
            outcome = "player_hit"
            for pid, p_data in participants.items():
                bet = p_data["bet"]
                if pid == hit_player_id:
                    score_change = -1 * bullet_count * bet
                    outcome_summary_parts.append(
                        f"玩家 {pid} 中弹，押注 {bet} 点，损失 {abs(score_change)} 分。"
                    )
                else:
                    score_change = 1 * bullet_count * bet
                    outcome_summary_parts.append(
                        f"玩家 {pid} 安全，押注 {bet} 点，获得 {score_change} 分。"
                    )
                score_changes[pid] = score_change
                self.data_manager.update_player_score(pid, score_change)
                self.data_manager.record_player_game_participation(pid, game_id)
        else:  # 无人中弹
            outcome = "all_safe"
            if participants:  # 只有当有参与者时才平分
                total_pot = bullet_count * 10
                # 如果参与人数为0，每人分0
                score_per_player = (
                    total_pot // len(participants) if len(participants) > 0 else 0
                )

                outcome_summary_parts.append(
                    f"所有子弹安全射出！总奖池 {total_pot} 点，"
                )
                if score_per_player > 0:
                    outcome_summary_parts.append(
                        f"每位参与者获得 {score_per_player} 分。"
                    )
                else:
                    outcome_summary_parts.append("但没有参与者瓜分奖池。")

                for pid, p_data in participants.items():
                    score_changes[pid] = score_per_player
                    self.data_manager.update_player_score(pid, score_per_player)
                    self.data_manager.record_player_game_participation(pid, game_id)
            else:
                outcome_summary_parts.append("所有子弹安全射出！但没有玩家参与。")

        # 保存游戏历史
        history_data = {
            "game_id": game_id,
            "group_id": self.group_id,
            "start_time": game_data["start_time"],
            "end_time": now_iso,
            "initiator_id": game_data["initiator_id"],
            "bullet_count": bullet_count,
            # "fatal_bullet_position": game_data["fatal_bullet_position"], # 移除
            "outcome": outcome,  # "player_hit" or "all_safe"
            "hit_player_id": hit_player_id,
            "participants_log": participants,  # 记录包含押注、是否命中等详细信息
            "score_changes": score_changes,  # 记录每个玩家的得分变化
        }
        self.data_manager.save_game_history(game_id, history_data)

        # 更新群组游戏状态
        self.data_manager.game_status["daily_games_ended_count"] += 1
        self.data_manager.game_status["last_game_end_date"] = datetime.now(
            timezone(timedelta(hours=8))
        ).strftime(
            "%Y-%m-%d"
        )  # 确保日期更新
        self.data_manager.game_status["current_game"] = None
        self.data_manager.save_game_status()

        summary = "\n".join(outcome_summary_parts)
        return {
            "game_id": game_id,
            "summary": summary,
            "scores": score_changes,
            "outcome": outcome,
        }

    def admin_end_game(self):
        """
        由管理员手动结束当前游戏。
        游戏将以"无人中弹"的方式结算。

        Returns:
            dict: 包含操作结果和信息的字典。
                  成功: {"success": True, "message": "游戏已由管理员结束..."}
                  失败: {"success": False, "message": "错误信息..."}
        """
        current_game_data = self.data_manager.game_status.get("current_game")

        if not current_game_data or current_game_data.get("status") != "running":
            return {"success": False, "message": "当前没有正在进行的轮盘游戏可以结束。"}

        game_id = current_game_data.get("id", "未知游戏")

        # 调用 _end_game，模拟无人中弹的情况
        # _end_game 会处理计分、保存历史、清空当前游戏状态等
        end_game_result = self._end_game(hit_player_id=None)

        admin_message = f"⚠️注意：本轮轮盘游戏 (ID: {game_id}) 已由管理员手动结束。\n"

        # 附加原有的结算信息
        full_message = admin_message + end_game_result.get(
            "summary", "游戏已结束，结算信息生成失败。"
        )

        return {
            "success": True,
            "message": full_message,
            "details": end_game_result,  # 包含原始结算详情
        }
