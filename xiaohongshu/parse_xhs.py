import pandas as pd

from tools.config_loader import BOT_WEBHOOK
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)


def parse_xhs_notes(file_path):
    """从Excel文件读取笔记数据"""
    # 读取Excel文件
    try:
        df = pd.read_excel(file_path, skiprows=1, engine='openpyxl')

        notes_data = []

        # 遍历每一行数据
        for index, row in df.iterrows():
            # 映射字段名
            title = str(row.get("笔记标题")) if pd.notna(row.get("笔记标题")) else "无标题笔记"
            post_time = row.get("首次发布时间", "未知时间")
            post_time = int(
                pd.to_datetime(str(post_time), format='%Y年%m月%d日%H时%M分%S秒')
                .tz_localize('Asia/Shanghai')  # 先本地化为上海时区
                .timestamp()  # 再转为 UTC 时间戳（秒，float）
                * 1000  # 转为毫秒
            )
            imp_count = row.get("曝光", 0)
            read_count = row.get("观看量", 0)  # 注意字段名变化
            like_count = row.get("点赞", 0)
            comment_count = row.get("评论", 0)
            share_count = row.get("分享", 0)
            fav_count = row.get("收藏", 0)
            cover_click_rate = row.get("封面点击率", 0)
            view_time_avg = row.get("人均观看时长", 0)

            # 与原代码保持相同的格式
            note_data = {
                "帖子名称": title,
                "发布时间": post_time,
                "曝光": int(imp_count) if pd.notna(imp_count) else 0,
                "观看": int(read_count) if pd.notna(read_count) else 0,
                "点赞": int(like_count) if pd.notna(like_count) else 0,
                "评论": int(comment_count) if pd.notna(comment_count) else 0,
                "分享": int(share_count) if pd.notna(share_count) else 0,
                "收藏": int(fav_count) if pd.notna(fav_count) else 0,
                "封面点击率": str(float(cover_click_rate) * 100) if pd.notna(cover_click_rate) else "0",
                "人均观看时长": int(view_time_avg) if pd.notna(view_time_avg) else 0,
            }
            log.info(note_data)

            notes_data.append(note_data)
    except Exception as e:
        log.error(e)
        raise


    return notes_data
