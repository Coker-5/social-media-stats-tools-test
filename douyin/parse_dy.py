# parse_dy.py
from tools.logstar import get_logger

log = get_logger()


def parse_douyin_notes(notes_res):
    """
    解析抖音笔记数据

    Args:
        notes_res: 抖音接口返回的笔记数据

    Returns:
        list: 解析后的笔记数据列表
    """
    notes_datas = []

    try:
        for index, note in enumerate(notes_res.get("items", [])):
            aweme_li = notes_res.get("aweme_list", [])[index]
            is_private = aweme_li.get("status", {}).get("is_private", False)

            if not is_private:
                link = aweme_li.get("share_url", "")  # 链接
                description = note.get("description", "")  # 帖子名称
                create_time = note.get("create_time", 0) * 1000  # 发布时间
                metrics = note.get("metrics", {})

                # 解析各项指标
                view_count = int(metrics.get("view_count", 0))  # 播放量
                like_count = int(metrics.get("like_count", 0))  # 点赞数
                comment_count = int(metrics.get("comment_count", 0))  # 评论数
                share_rate = int(float(metrics.get("share_rate", 0)))  # 分享数
                favorite_count = int(metrics.get("favorite_count", 0))  # 收藏数

                # 计算比率（转换为百分比）
                completion_rate_5s = str(round(float(metrics.get("completion_rate_5s", 0)) * 100, 2))  # 5s完播率
                bounce_rate_2s = str(round(float(metrics.get("bounce_rate_2s", 0)) * 100, 1))  # 2s跳出率
                avg_view_second = int(float(metrics.get("avg_view_second", 0)))  # 平均播放时长
                completion_rate = str(round(float(metrics.get("completion_rate", 0)) * 100, 1))  # 完播率

                # 构建笔记数据字典
                note_data = {
                    "帖子名称": description,
                    "发布时间": create_time,
                    "播放量": view_count,
                    "点赞数": like_count,
                    "评论数": comment_count,
                    "分享数": share_rate,
                    "收藏数": favorite_count,
                    "5秒完播率": completion_rate_5s,
                    "2秒跳出率": bounce_rate_2s,
                    "平均播放时长": avg_view_second,
                    "完播率": completion_rate,
                    "帖子链接": {
                        "text": description,
                        "link": link
                    },
                }

                notes_datas.append(note_data)
                log.info(note_data)

    except Exception as e:
        log.error(f"解析笔记数据时出错: {e}")
        raise

    return notes_datas