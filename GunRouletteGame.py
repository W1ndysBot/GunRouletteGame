class GunRouletteGame:
    """
    枪战轮盘游戏类

    负责管理枪战轮盘游戏的状态、玩家、分数等。
    """

    def __init__(self, group_id):
        self.group_id = group_id
        self.game_status = None
        self.game_players = []
        self.game_score = 0
