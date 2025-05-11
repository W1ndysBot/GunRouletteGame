class Menu:
    """
    菜单类，负责显示菜单。
    """

    def get_menu(self):
        self.menu = "----------------- \n"
        self.menu += "轮盘菜单\n"
        self.menu += "-----------------\n"
        self.menu += "卷卷轮盘：开始一场轮盘游戏\n"
        self.menu += "卷卷轮盘 [子弹数]：开始一场轮盘游戏，默认6颗子弹\n"
        self.menu += "卷卷开枪：参与一场轮盘游戏\n"
        self.menu += "卷卷开枪 [押注点数]：参与一场轮盘游戏，默认押注1点\n"
        self.menu += "-----------------\n"
        return self.menu
