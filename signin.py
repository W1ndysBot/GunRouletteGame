"""
签到系统
"""

import os
import json
from datetime import datetime, timedelta, timezone
from app.scripts.GunRouletteGame.DataManager import DataManager  # 确保导入

# 签到记录文件名
SIGNIN_RECORDS_FILENAME = "signin_records.json"

# 签到奖励配置
SIGNIN_BASE_POINTS = 10  # 基础签到分数
SIGNIN_BONUS_POINTS = {  # 名次额外奖励
    1: 50,  # 第一名
    2: 30,  # 第二名
    3: 20,  # 第三名
}
SIGNIN_START_HOUR_UTC8 = 8  # 签到开始时间 (东八区)
SIGNIN_END_HOUR_UTC8 = 23  # 签到结束时间 (东八区)


class SignIn:
    def __init__(self, group_id, user_id):  # 移除 data_manager 参数
        self.group_id = str(group_id)
        self.user_id = str(user_id)
        self.data_manager = DataManager(group_id=self.group_id)  # 内部实例化
        # 构建数据目录路径，与 DataManager 保持一致性
        base_data_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "data",
            "GunRouletteGame",
        )
        self.group_data_dir = os.path.join(base_data_path, self.group_id)
        os.makedirs(self.group_data_dir, exist_ok=True)  # 确保群组数据目录存在

        self.records_file_path = os.path.join(
            self.group_data_dir, SIGNIN_RECORDS_FILENAME
        )
        self.signin_records = self._load_signin_records()

    def _get_utc8_now(self):
        """获取当前的东八区时间"""
        return datetime.now(timezone(timedelta(hours=8)))

    def _load_signin_records(self):
        """
        加载指定群组的签到记录。
        文件内容格式：
        {
          "YYYY-MM-DD": { // 东八区日期字符串
            "sign_ins": [
              {"user_id": "xxx", "timestamp": "iso_timestamp_utc8", "order": 1, "points_awarded": 60},
              {"user_id": "yyy", "timestamp": "iso_timestamp_utc8", "order": 2, "points_awarded": 40}
            ]
          },
          // ... 其他日期的记录
        }
        """
        if os.path.exists(self.records_file_path):
            try:
                with open(self.records_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                # 文件损坏或未找到（理论上FileNotFound已被os.path.exists处理）
                return {}  # 返回空字典，将在保存时创建新文件
        return {}  # 文件不存在，返回空字典

    def _save_signin_records(self):
        """保存签到记录到文件。"""
        try:
            with open(self.records_file_path, "w", encoding="utf-8") as f:
                json.dump(self.signin_records, f, ensure_ascii=False, indent=4)
        except IOError as e:
            # 实际应用中应处理这个错误，例如logging
            # logging.error(f"Error saving sign-in records for group {self.group_id}: {e}")
            print(
                f"Error saving sign-in records for group {self.group_id}: {e}"
            )  # 暂时用print
            pass  # 简单处理，避免程序崩溃

    def perform_signin(self):
        """
        处理用户签到逻辑。

        Returns:
            dict: 包含签到结果和消息的字典。
                  例如: {"success": True, "message": "签到成功...", "points_awarded": 20}
                        {"success": False, "message": "错误信息..."}
        """
        now_utc8 = self._get_utc8_now()
        today_date_str = now_utc8.strftime("%Y-%m-%d")

        # 1. 检查签到时间
        if not (SIGNIN_START_HOUR_UTC8 <= now_utc8.hour < SIGNIN_END_HOUR_UTC8):
            return {
                "success": False,
                "message": f"不在签到时间内哦！请在每天东八区 {SIGNIN_START_HOUR_UTC8}:00 - {SIGNIN_END_HOUR_UTC8-1}:59 之间签到。",
            }

        # 2. 获取或初始化当天的签到记录
        daily_records = self.signin_records.setdefault(today_date_str, {"sign_ins": []})

        # 3. 检查用户是否已签到
        for record in daily_records["sign_ins"]:
            if record["user_id"] == self.user_id:
                return {
                    "success": False,
                    "message": f"您今天已经签到过了，获得了 {record.get('points_awarded', '未知')} 点积分。",
                }

        # 4. 执行签到
        signin_order = len(daily_records["sign_ins"]) + 1
        base_points = SIGNIN_BASE_POINTS
        bonus_points = SIGNIN_BONUS_POINTS.get(signin_order, 0)
        total_points_awarded = base_points + bonus_points

        # 5. 添加签到记录
        signin_entry = {
            "user_id": self.user_id,
            "timestamp": now_utc8.isoformat(),
            "order": signin_order,
            "points_awarded": total_points_awarded,
        }
        daily_records["sign_ins"].append(signin_entry)
        self._save_signin_records()

        # 6. 更新玩家总积分 (通过 self.data_manager 实例)
        self.data_manager.update_player_score(self.user_id, total_points_awarded)
        # 确保 DataManager 也保存了玩家数据的更改
        # self.data_manager.save_player_data(self.user_id, self.data_manager.get_player_data(self.user_id)) # update_player_score 内部应该已经保存了

        # 7. 构建成功消息
        message = f"🎉签到成功！您是今天第 {signin_order} 位签到的勇士！\n"
        message += f"获得了基础积分 {base_points} 点。"
        if bonus_points > 0:
            message += f"\n额外获得了第 {signin_order} 名奖励积分 {bonus_points} 点！"
        message += f"\n总共获得 {total_points_awarded} 点积分。"

        # 可以考虑增加提示今日签到人数等
        message += f"\n今日已有 {signin_order} 人签到。"

        return {
            "success": True,
            "message": message,
            "points_awarded": total_points_awarded,
            "order": signin_order,
        }
