import pandas as pd
from datetime import datetime
import re


def parse_sph_notes(file_path):
    """
    从CSV文件读取视频号帖子数据。
    """
    # --- 配置区域：在此定义映射关系 ---
    # 格式: {"CSV列名": "程序内部字段名"}
    COLUMN_MAPPING = {
        "视频描述": "title",
        "发布时间": "pub_time",
        "播放量": "play_count",
        "喜欢": "dianzan_count",
        "推荐": "heart_count",
        "评论量": "comment_count",
        "分享量": "share_count",
        "完播率": "completion_rate",
        "平均播放时长": "avg_watch_time"
    }

    try:
        # 1. 读取CSV
        df = pd.read_csv(file_path, encoding='utf-8')

        # 2. 验证列是否存在
        csv_columns = df.columns.tolist()
        missing_cols = [col for col in COLUMN_MAPPING.keys() if col not in csv_columns]

        if missing_cols:
            # 如果发现映射中的列在CSV中不存在，抛出错误
            raise KeyError(f"列错误: {', '.join(missing_cols)}")

        # 3. 重命名并仅保留需要的列 (根据映射字典)
        df_selected = df[list(COLUMN_MAPPING.keys())].rename(columns=COLUMN_MAPPING)

        notes_data = []

        for index, row in df_selected.iterrows():
            # --- 提取字段（使用映射后的内部名称） ---
            title = str(row["title"]) if pd.notna(row["title"]) else "无标题视频"

            # --- 发布时间处理 ---
            pub_time_raw = row["pub_time"]
            if pd.isna(pub_time_raw) or str(pub_time_raw).strip() == "":
                timestamp_ms = 0
            else:
                dt = datetime.strptime(str(pub_time_raw).strip(), "%Y/%m/%d")
                timestamp_ms = int(dt.timestamp()) * 1000

            # --- 数值类字段处理 ---
            def to_int(val):
                return int(val) if pd.notna(val) and str(val).strip() != "-" else 0

            play_count = to_int(row["play_count"])
            dianzan_count = to_int(row["dianzan_count"])
            heart_count = to_int(row["heart_count"])
            comment_count = to_int(row["comment_count"])
            share_count = to_int(row["share_count"])

            # --- 完播率处理 ---
            completion_rate_raw = str(row["completion_rate"])
            if pd.isna(row["completion_rate"]) or completion_rate_raw == "-":
                completion_rate_raw = "0"
            else:
                match = re.search(r"([\d.]+)%", completion_rate_raw)
                completion_rate_raw = match.group(1) if match else "0"

            # --- 平均播放时长处理 ---
            avg_watch_time_raw = row["avg_watch_time"]
            if pd.isna(avg_watch_time_raw) or str(avg_watch_time_raw) == "-":
                avg_watch_time_sec = 0.0
            else:
                avg_val = str(avg_watch_time_raw).replace("秒", "").strip()
                avg_watch_time_sec = float(avg_val) if avg_val else 0.0

            note_data = {
                "帖子名称": title,
                "发布时间": timestamp_ms,
                "播放量": play_count,
                "点赞数": dianzan_count,
                "喜欢数": heart_count,
                "评论数": comment_count,
                "分享数": share_count,
                "完播率": completion_rate_raw,
                "人均播放时长": avg_watch_time_sec,
            }

            notes_data.append(note_data)

        return notes_data

    except Exception as e:
        print(f"解析过程中发生错误: {type(e).__name__}: {e}")
        raise