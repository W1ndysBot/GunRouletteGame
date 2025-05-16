class Menu:
    """
    菜单类，负责显示菜单。
    """

    def get_menu(self):
        self.menu = "轮盘菜单\n"
        self.menu += "-----------------\n"
        self.menu += "开始轮盘+子弹数：开始一场轮盘游戏，默认6颗子弹\n"
        self.menu += "biu+押注点数：参与一场轮盘游戏，默认押注1点\n"
        self.menu += "结束轮盘：结束一场轮盘游戏\n"
        self.menu += "轮盘排行：查看轮盘排行榜\n"
        self.menu += "我的轮盘：查看我的轮盘信息\n"
        self.menu += "轮盘签到：每日签到获取积分"
        return self.menu
