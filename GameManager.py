"""
游戏管理类

负责管理每场游戏的相关数据，包括游戏状态、玩家、分数等。
"""

from app.scripts.GunRouletteGame.DataManager import DataManager


class GameManager:
    def __init__(self, group_id, bullet_count):
        self.group_id = group_id
        self.game_status = DataManager(group_id).get_game_status()
        self.bullet_count = bullet_count

    def start_game(self):
        """
        开始一场枪战轮盘游戏
        """
        # 检查是否有正在进行的游戏
        if self.game_status["game_status"] == "running":
            return {"success": False, "message": "当前有正在进行的游戏"}
        # 检查是否达到最大游戏数量
        elif self.game_status["game_count"] >= 5:
            return {"success": False, "message": "当前群组达到今日最大游戏数量"}
