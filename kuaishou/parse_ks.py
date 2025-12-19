# parse_ks.py
from tools.logstar import get_logger

log = get_logger()


def parse_ks_photo_list_data(photo_list_response):
    """
    解析快手帖子列表数据接口的响应
    返回帖子基本信息列表
    """
    try:
        notes_basic_info = []

        if photo_list_response.get("result") != 1:
            log.error(f"快手接口返回失败: {photo_list_response}")
            return notes_basic_info

        photo_list = photo_list_response.get("data", {}).get("photoList", {})
        photo_items = photo_list.get("photoItems", [])

        for item in photo_items:
            # 提取帖子基础信息
            title = item.get("title", "无标题")
            photo_id = item.get("photoId", "")
            publish_time = item.get("publishTime", 0)
            play_count = item.get("playCount", 0)
            like_count = item.get("likeCount", 0)
            comment_count = item.get("commentCount", 0)
            collect_count = item.get("collectCount", 0)

            notes_basic_info.append({
                "photo_id": photo_id,
                "title": title,
                "publish_time": publish_time,
                "play_count": int(play_count),
                "like_count": int(like_count),
                "comment_count": int(comment_count),
                "collect_count": int(collect_count)
            })

        return notes_basic_info

    except Exception as e:
        log.error(f"解析快手帖子列表数据失败: {str(e)}")
        raise


def parse_ks_photo_detail_data(detail_response):
    """
    解析快手帖子详细数据接口的响应
    返回帖子详细数据字典
    """
    try:
        detail_data = {
            "播放量": 0,
            "平均播放时长": 0,
            "封面点击率": 0,
            "2s跳出率": 0,
            "5s完播率": 0,
            "完播率": 0
        }

        if detail_response.get("result") != 1:
            log.warning(f"快手详细数据接口返回失败: {detail_response}")
            return detail_data

        trend_list = detail_response.get("data", {}).get("trendList", [])

        # 提取trendList中的sumCount值
        for trend_item in trend_list:
            name = trend_item.get("name", "")
            sum_count = trend_item.get("sumCount", 0)

            if name in detail_data:
                detail_data[name] = sum_count
            elif name == "播放量":
                detail_data["播放量"] = sum_count
            elif name == "平均播放时长":
                detail_data["平均播放时长"] = sum_count
            elif name == "封面点击率":
                detail_data["封面点击率"] = sum_count
            elif name == "2s跳出率":
                detail_data["2s跳出率"] = sum_count
            elif name == "5s完播率":
                detail_data["5s完播率"] = sum_count
            elif name == "完播率":
                detail_data["完播率"] = sum_count

        return detail_data

    except Exception as e:
        log.error(f"解析快手帖子详细数据失败: {str(e)}")
        raise e


def format_note_data(basic_info, detail_data):
    """
    格式化帖子数据，将基础信息和详细信息合并
    """
    try:
        note_data = {
            "帖子名称": basic_info.get("title", "无标题"),
            "发布时间": basic_info.get("publish_time", 0),
            "播放量": basic_info.get("play_count", 0),  # 使用列表接口的播放量
            "点赞数": basic_info.get("like_count", 0),
            "评论数": basic_info.get("comment_count", 0),
            "收藏数": basic_info.get("collect_count", 0),
            "封面点击率": f"{detail_data['封面点击率']}" if detail_data['封面点击率'] > 0 else "0",
            "人均播放时长": round(detail_data['平均播放时长'] / 1000, 2) if detail_data['平均播放时长'] > 0 else 0,
            "完播率": f"{detail_data['完播率']}" if detail_data['完播率'] > 0 else "0",
            "2s跳出率": f"{detail_data['2s跳出率']}" if detail_data['2s跳出率'] > 0 else "0",
            "5s完播率": f"{detail_data['5s完播率']}" if detail_data['5s完播率'] > 0 else "0",
            "帖子链接": {
                "text": basic_info.get("title", "无标题"),
                "link": f"https://m.gifshow.com/fw/photo/{basic_info.get('photo_id', '')}"
            },
        }
        return note_data

    except Exception as e:
        log.error(f"格式化帖子数据失败: {str(e)}")
        raise e
