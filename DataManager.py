import os
import json
import uuid
from datetime import datetime, timezone, timedelta


class DataManager:
    """
    数据管理类

    负责管理游戏数据，包括游戏状态、玩家、分数等。
    """

    def __init__(self, group_id):
        base_data_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "data",
            "GunRouletteGame",
        )
        self.data_dir = os.path.join(base_data_path, str(group_id))
        self.game_history_dir = os.path.join(self.data_dir, "game_history")
        self.player_data_dir = os.path.join(self.data_dir, "player_data")

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.game_history_dir, exist_ok=True)
        os.makedirs(self.player_data_dir, exist_ok=True)

        self.group_id = str(group_id)
        self.game_status = self._load_game_status()

    def _load_game_status(self):
        """
        加载或初始化游戏状态文件。
        文件内容格式：
        {
            "group_id": "str",              # 群ID
            "daily_games_ended_count": 0, # 当前群组今日已结束的游戏数量
            "last_game_end_date": "YYYY-MM-DD", # 上次游戏结束日期，用于重置每日计数
            "current_game": null or {      # 当前游戏详情，null表示无游戏进行
                "id": "unique_game_id",    # 当前游戏的唯一ID
                "status": "running",       # 当前游戏状态 ("idle", "running")
                "start_time": "iso_timestamp", # 当前游戏开始时间
                "initiator_id": "user_id", # 当前游戏发起者
                "bullet_count": 6,         # 当前游戏初始子弹数量 (总膛数)
                "real_bullet_initially_present": True, # 游戏开始时是否真的有子弹
                "is_bullet_fired_this_game": False,   # 本局游戏中子弹是否已被击发
                "shots_fired_count": 0,    # 已开枪次数
                "participants": {          # 参与者信息 {user_id: {"bet": int, "shot_order": int, "is_hit": bool}}
                    # "player1_id": {"bet": 2, "shot_order": 0, "is_hit": False}
                }
            }
        }
        """
        status_file = os.path.join(self.data_dir, "game_status.json")
        default_game_status = {
            "group_id": self.group_id,
            "daily_games_ended_count": 0,
            "last_game_end_date": datetime.now(timezone(timedelta(hours=8))).strftime(
                "%Y-%m-%d"
            ),
            "current_game": None,
        }

        if os.path.exists(status_file):
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    loaded_status = json.load(f)
                    # 可以在这里添加版本迁移或字段检查逻辑
                    return loaded_status
            except (json.JSONDecodeError, FileNotFoundError):
                # 文件损坏或不存在，使用默认值并保存
                with open(status_file, "w", encoding="utf-8") as f:
                    json.dump(default_game_status, f, ensure_ascii=False, indent=4)
                return default_game_status
        else:
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(default_game_status, f, ensure_ascii=False, indent=4)
            return default_game_status

    def save_game_status(self):
        """
        保存当前游戏状态到文件 game_status.json
        """
        status_file = os.path.join(self.data_dir, "game_status.json")
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(self.game_status, f, ensure_ascii=False, indent=4)

    def get_game_history(self, game_id):
        """
        获取指定 game_id 的游戏历史记录。
        """
        history_file = os.path.join(self.game_history_dir, f"{game_id}.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None  # 文件损坏
        return None

    def save_game_history(self, game_id, game_data):
        """
        保存单场游戏历史记录到 data_dir/群号/game_history/游戏ID.json
        game_data 结构示例:
        {
            "game_id": "unique_game_id",
            "group_id": "group_id",
            "start_time": "iso_timestamp",
            "end_time": "iso_timestamp",
            "initiator_id": "user_id",
            "bullet_count": 6,
            "outcome": "player_hit" / "all_safe",
            "hit_player_id": "user_id" / null,
            "participants_log": { # user_id: {"bet": int, "score_change": int}
                # "player1_id": {"bet": 2, "score_change": 12}
            }
        }
        """
        history_file = os.path.join(self.game_history_dir, f"{game_id}.json")
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(game_data, f, ensure_ascii=False, indent=4)

    def get_player_data(self, user_id):
        """
        获取指定玩家的数据 data_dir/群号/player_data/玩家QQ号.json
        返回玩家数据字典，如果玩家文件不存在或解析失败，则返回默认玩家数据。
        """
        player_file = os.path.join(self.player_data_dir, f"{user_id}.json")
        default_player_data = {
            "user_id": str(user_id),
            "total_score": 0,
            "games_participated_ids": [],
            "games_initiated_timestamps": [],  # 用于检查发起游戏频率
        }
        if os.path.exists(player_file):
            try:
                with open(player_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # 文件损坏，返回默认数据，但不覆盖原文件，让save时重建
                return default_player_data
        return default_player_data

    def save_player_data(self, user_id, player_data):
        """
        保存玩家数据到 data_dir/群号/player_data/玩家QQ号.json
        """
        player_file = os.path.join(self.player_data_dir, f"{user_id}.json")
        with open(player_file, "w", encoding="utf-8") as f:
            json.dump(player_data, f, ensure_ascii=False, indent=4)

    # 辅助方法，可以在 GameManager 中调用
    def update_player_score(self, user_id, score_change):
        player_data = self.get_player_data(user_id)
        player_data["total_score"] += score_change
        self.save_player_data(user_id, player_data)

    def record_player_game_participation(self, user_id, game_id):
        player_data = self.get_player_data(user_id)
        if game_id not in player_data["games_participated_ids"]:
            player_data["games_participated_ids"].append(game_id)
        self.save_player_data(user_id, player_data)

    def record_player_game_initiation(self, user_id):
        player_data = self.get_player_data(user_id)
        player_data["games_initiated_timestamps"].append(
            datetime.now(timezone(timedelta(hours=8))).isoformat()
        )
        # 可以考虑限制列表长度，例如只保留最近N次记录
        self.save_player_data(user_id, player_data)

    def get_rank(self):
        """
        获取轮盘排行榜
        返回列表，每个元素是一个字典，包含玩家ID、总得分
        """
        # 获取所有玩家数据
        player_data_dir = os.path.join(self.data_dir, "player_data")
        player_files = [f for f in os.listdir(player_data_dir) if f.endswith(".json")]

        # 读取玩家数据并排序
        players = []
        for player_file in player_files:
            with open(
                os.path.join(player_data_dir, player_file), "r", encoding="utf-8"
            ) as f:
                player_data = json.load(f)
                players.append(
                    {
                        "user_id": player_data["user_id"],
                        "total_score": player_data["total_score"],
                    }
                )

        # 按照分数从高到低排序
        players.sort(key=lambda x: x["total_score"], reverse=True)

        return players

    def get_my_roulette(self, user_id):
        """
        获取指定玩家的数据
        """
        player_data = self.get_player_data(user_id)
        # 解析数据，拼接为字符串
        message = f"玩家 {user_id} 的轮盘信息：\n"
        message += "-----------------\n"
        message += f"总得分：{player_data['total_score']}\n"
        message += f"参与游戏次数：{len(player_data['games_participated_ids'])}\n"
        message += f"发起游戏次数：{len(player_data['games_initiated_timestamps'])}\n"
        message += "-----------------\n"
        return message
