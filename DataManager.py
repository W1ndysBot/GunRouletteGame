import os
import json
import uuid


class DataManager:
    """
    数据管理类

    负责管理游戏数据，包括游戏状态、玩家、分数等。
    """

    def __init__(self, group_id):
        self.data_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "data",
            "GunRouletteGame",
            group_id,
        )
        os.makedirs(self.data_dir, exist_ok=True)
        self.group_id = group_id
        self.game_status = self.get_game_status()

    def get_game_status(self):
        """
        获取游戏状态文件的内容
        文件内容格式：
        {
            "group_id": "group_id",  # 群ID
            "game_count": 0,  # 当前群组今日已结束的游戏数量
            "game_id": "unique_game_id",  # 当前游戏的唯一ID
            "game_status": "running",  # 当前游戏状态
            "game_start_time": "2021-01-01 00:00:00",  # 当前游戏开始时间
            "game_initiator": "user_id",  # 当前游戏发起者
            "bullet_count": 6,  # 当前游戏初始子弹数量
            "bullet_position": 0,  # 当前游戏剩余子弹数量
        }
        """
        default_game_status = {
            "group_id": self.group_id,
            "game_count": 0,
            "game_id": None,
            "game_status": "idle",
            "game_start_time": None,
            "game_initiator": None,
            "bullet_count": 6,
            "bullet_position": 0,
        }
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        status_file = os.path.join(self.data_dir, "game_status.json")
        if os.path.exists(status_file):
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    self.game_status = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                # 如果文件解析失败，返回默认数据，并创建新的游戏状态文件
                self.game_status = default_game_status
                with open(status_file, "w", encoding="utf-8") as f:
                    json.dump(self.game_status, f)
        else:
            # 如果文件不存在，返回默认数据，并创建新的游戏状态文件
            self.game_status = default_game_status
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(self.game_status, f)

        return self.game_status

    def save_game_status(self):
        """
        保存游戏状态到文件
        """
        with open(
            os.path.join(self.data_dir, "game_status.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(self.game_status, f)

    def get_one_game_status(self, game_id):
        """
        获取单个游戏状态
        """
        game_status_file = os.path.join(
            self.data_dir, "game_history", f"{game_id}.json"
        )
        if os.path.exists(game_status_file):
            with open(game_status_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def save_one_game_status(self, game_id, game_status):
        """
        保存单个游戏状态到文件
        """
        with open(
            os.path.join(self.data_dir, "game_history", f"{game_id}.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(game_status, f)
