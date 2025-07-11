# GunRouletteGame

W1ndysBot 的biu轮盘游戏功能模块

## 基本命令

- 总开关：`grg`
- 开始一场轮盘游戏：`开始轮盘`
- 参与这场轮盘游戏：`biu`
- 游戏命令和规则解释：`轮盘菜单`

## 游戏规则

当一名玩家使用`开始轮盘`命令时，会开始一场轮盘游戏，可以加参数，表示几颗biubiu最低且默认为 6 颗，每个群每天只能开 5 场轮盘游戏。单个玩家每小时只能发起 1 场游戏（防刷分）。

轮盘游戏开始后，群友可以发送`biu`命令参与游戏，每个人只能biu一次，可以加参数，表示置权点数。每次只能押 1~3 点（防止无脑高分）。

玩家biu时，触发惩罚的概率 = 1 / (剩余空弹数 + 1)。

举例：6 弹轮盘，第 1 人biu概率 = 1/6 ≈16.6%，第 2 人 = 1/5=20%……越往后风险越高。

当有玩家触发惩罚后，本场游戏结束，播报惩罚群友，并播报本场游戏得分情况。

没被触发惩罚的群友会获得 `1*biubiu数*置权点数` 分，触发惩罚的群友会减 `1*biubiu数*置权点数` 分。若无人中弹，所有参与者平分 biubiu数 ×10 分（皆大欢喜）。

## 代码实现补充

- 场次的存储路径为`data_dir/群号/game_history/`，文件名称为`游戏ID.json`。需要有每局场次的记录，包括参与者、biubiu数、置权点数、得分情况、致命biubiu位置等。
- 本群当前状态以及该群的数据存储路径为`data_dir/群号/`，文件名称为`game_status.json`。主要包括当前群组每天已结束的游戏数量、当前游戏的唯一 ID、当前游戏状态、当前游戏开始时间、当前游戏发起者、当前游戏剩余biubiu数量、当前游戏剩余biubiu位置等必要信息。
- 玩家数据存储路径为`data_dir/群号/player_data/`，文件名称为`玩家QQ号.json`。
- 玩家数据包括玩家 QQ 号、玩家得分，玩家参与场次，玩家参与每场时间。
