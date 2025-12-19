import pandas as pd
from datetime import datetime
import re


def parse_sph_notes(file_path):
    """从CSV文件读取视频号帖子数据"""
    try:
        # 读取CSV文件（注意编码和分隔符）
        df = pd.read_csv(file_path, encoding='utf-8')

        notes_data = []

        for index, row in df.iterrows():
            # 提取字段
            title = str(row.get("视频描述", "无标题视频"))

            # 处理发布时间：格式为 '2025/12/18'
            pub_time_str = str(row.get("发布时间", "")).strip()
            if pub_time_str and pub_time_str != "nan":
                # 默认设为当天 12:00:00
                dt = datetime.strptime(pub_time_str, "%Y/%m/%d")
                # 假设为北京时间（UTC+8）
                timestamp_ms = int(dt.timestamp()) * 1000
            else:
                timestamp_ms = 0

            # 播放量作为曝光和观看
            play_count = row.get("播放量", 0)
            play_count = int(play_count) if pd.notna(play_count) else 0

            # 点赞、评论、分享
            like_count = row.get("喜欢", 0)
            comment_count = row.get("评论量", 0)
            share_count = row.get("分享量", 0)

            # 完播率：如 "4.92%" → 转为 "4.92"
            completion_rate = row.get("完播率", "0%")
            if pd.isna(completion_rate) or completion_rate == "-":
                cover_click_rate_str = "0"
            else:
                # 提取数字部分
                match = re.search(r"([\d.]+)%", str(completion_rate))
                cover_click_rate_str = match.group(1) if match else "0"

            # 平均播放时长（秒），保留整数
            avg_watch_time = row.get("平均播放时长", 0)
            if pd.isna(avg_watch_time) or avg_watch_time == "-":
                avg_watch_time_sec = 0
            else:
                avg_watch_time_sec = int(float(avg_watch_time))

            note_data = {
                "帖子名称": title,
                "发布时间": timestamp_ms,
                "曝光": play_count,
                "观看": play_count,
                "点赞": int(like_count) if pd.notna(like_count) else 0,
                "评论": int(comment_count) if pd.notna(comment_count) else 0,
                "分享": int(share_count) if pd.notna(share_count) else 0,
                "收藏": 0,  # 视频号 CSV 中无收藏字段
                "封面点击率": cover_click_rate_str,
                "人均观看时长": avg_watch_time_sec,
            }

            print(note_data)  # 或 log.info(note_data)
            notes_data.append(note_data)

        return notes_data

    except Exception as e:
        print(f"解析失败: {e}")
        raise