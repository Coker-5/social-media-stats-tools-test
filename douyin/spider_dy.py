import re
from datetime import datetime, timedelta

from DrissionPage import Chromium
from tools.data_clean import cleaning
from tools.feishu_bitable_uploader import FeishuBitableWriter
from tools.logstar import get_logger
from tools.config_loader import (BASE_TOKEN, TABLE_DY_NOTES, TABLE_DY_ACCOUNTS, BOT_WEBHOOK, DEVELOPERS_ID_LIST)
from douyin.parse_dy import parse_douyin_notes  # 导入解析函数
from tools.send_feishu import FeishuBot

log = get_logger()
tab = None
bot = FeishuBot(BOT_WEBHOOK)


# 账号维度数据
def spider_douyin_account():
    # 首页
    log.info("开始采集账号维度数据...")
    tab.get(url='https://creator.douyin.com')
    tab.wait(6)

    # 粉丝数据
    parent_ele = tab.ele('.statics-kyUhqC')
    numbers = parent_ele.eles('.number-No6ev9')
    numbers_text = [i.text for i in numbers]
    numbers_text = cleaning(numbers_text)

    fans_num = numbers_text[1]  # 粉丝
    likes_num = numbers_text[2]  # 获赞

    # 浏览数据
    play_count = 0  # 播放量
    homepage_views = 0  # 主页访问量
    likes = 0  # 作品点赞
    shares = 0  # 作品分享
    comments = 0  # 作品评论
    followers = 0  # 净增粉丝

    yesterday_play_count = 0  # 播放量
    yesterday_homepage_views = 0  # 主页访问量
    yesterday_likes = 0  # 作品点赞
    yesterday_shares = 0  # 作品分享
    yesterday_comments = 0  # 作品评论
    yesterday_followers = 0  # 净增粉丝

    # 近七天
    parent_ele = tab.eles('.number-vDKr2F')
    parent_ele_text = [i.text for i in parent_ele]
    parent_ele_text = cleaning(parent_ele_text)
    if parent_ele_text and len(parent_ele_text) > 3:
        play_count = parent_ele_text[0]  # 播放量
        homepage_views = parent_ele_text[1]  # 主页访问量
        likes = parent_ele_text[2]  # 作品点赞
        shares = parent_ele_text[3]  # 作品分享
        comments = parent_ele_text[4]  # 作品评论
        followers = parent_ele_text[5]  # 净增粉丝

    # 昨天
    tab.ele("@role=combobox").click()
    option = tab.eles("@role=option")
    option[0].click()

    tab.wait(3)

    parent_ele = tab.eles('.number-vDKr2F')
    parent_ele_text = [i.text for i in parent_ele]
    parent_ele_text = cleaning(parent_ele_text)
    if parent_ele_text and len(parent_ele_text) > 3:
        yesterday_play_count = parent_ele_text[0]  # 播放量
        yesterday_homepage_views = parent_ele_text[1]  # 主页访问量
        yesterday_likes = parent_ele_text[2]  # 作品点赞
        yesterday_shares = parent_ele_text[3]  # 作品分享
        yesterday_comments = parent_ele_text[4]  # 作品评论
        yesterday_followers = parent_ele_text[5]  # 净增粉丝

    accont_data = {
        "粉丝": int(fans_num),
        "获赞": int(likes_num),
        "近7天播放量": int(play_count),
        "近7天主页访问量": int(homepage_views),
        "近7天点赞": int(likes),
        "近7天分享": int(shares),
        "近7天评论": int(comments),
        "近7天净增粉丝": int(followers),

        "昨日播放量": int(yesterday_play_count),
        "昨日主页访问量": int(yesterday_homepage_views),
        "昨日点赞": int(yesterday_likes),
        "昨日分享": int(yesterday_shares),
        "昨日评论": int(yesterday_comments),
        "昨日净增粉丝": int(yesterday_followers),
    }

    log.info(accont_data)

    return accont_data


# 帖子维度数据
def spider_douyin_notes():
    # 内容管理-作品管理-作品
    log.info("开始采集帖子维度数据...")
    tab.get(url='https://creator.douyin.com/creator-micro/content/manage')
    tab.wait(2)
    tab.change_mode('s')

    has_more = True
    max_cursor = 0  # 使用返回的时间戳作为翻页标识
    notes_datas = []

    while has_more:
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "priority": "u=1, i",
            "referer": "https://creator.douyin.com/creator-micro/content/manage",
            "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }
        url = "https://creator.douyin.com/janus/douyin/creator/pc/work_list"
        params = {
            "status": "0",
            "count": "12",
            "max_cursor": max_cursor,
            "scene": "star_atlas",
            "device_platform": "android",
            "aid": "1128"
        }
        try:
            tab.get(url, headers=headers, params=params)
            if tab.response.ok:
                notes_res = tab.response.json()
                max_cursor = notes_res.get("max_cursor", 0)
                has_more = notes_res.get('has_more', False)

                page_notes = parse_douyin_notes(notes_res)
                notes_datas.extend(page_notes)

        except Exception as e:
            log.error(f"获取笔记数据时出错: {e}")
            raise
        finally:
            tab.wait(1.5)

    return notes_datas


# 私信数据


# 获取抖音创作者指定时间范围发布的视频
def get_recent_month_videos(tab, initial_cursor=None, days=720):
    """
    获取抖音创作者近一个月发布的视频
    Args:
        initial_cursor: 初始cursor，如果不传则从第一页开始
        days: 近多少天，默认30天
    Returns:
        近一个月发布的视频列表
    """
    # 计算近一个月的时间点
    one_month_ago = datetime.now() - timedelta(days=days)

    videos = []
    cursor = initial_cursor
    has_more = True
    request_count = 0
    max_requests = 100  # 防止无限循环

    # 从中文日期字符串解析时间
    def parse_chinese_date(date_str: str) -> datetime:
        # 匹配格式: "发布于2025年12月30日 21:26"
        pattern = r'发布于(\d{4})年(\d{1,2})月(\d{1,2})日 (\d{1,2}):(\d{1,2})'
        match = re.search(pattern, date_str)
        if match:
            year, month, day, hour, minute = map(int, match.groups())
            return datetime(year, month, day, hour, minute)
        return datetime.min

    while has_more and request_count < max_requests:
        # 构建请求URL
        url = f'https://creator.douyin.com/aweme/v1/creator/item/list/?cursor={cursor or ""}&aid=2906'

        # 请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "agw-js-conv": "str",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://creator.douyin.com/creator-micro/interactive/comment",
            "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-secsdk-csrf-token": "000100000001af774ad51143a894453b39afdfc43b91845b10858a7c8740fcc65fee54dd5bfb1888608ec7208bd7"
        }

        try:
            tab.get(url, headers=headers, timeout=30)
            tab.response.raise_for_status()

            data = tab.response.json()

            # 更新分页信息
            cursor = data['cursor']
            has_more = data['has_more']
            request_count += 1

            # 处理当前页的视频
            for item in data.get('item_info_list', []):
                # 解析发布时间
                create_time_str = item['create_time']
                # 转换为datetime对象
                try:
                    publish_time = parse_chinese_date(create_time_str)

                    # 检查是否在指定时间范围
                    if publish_time >= one_month_ago:
                        video_info = {
                            'title': item['title'],
                            'item_id': item['item_id'],
                            'item_id_plain': item['item_id_plain'],
                            'publish_time': publish_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'item_link': item['item_link'],
                            'comment_count': item['comment_count'],
                        }
                        videos.append(video_info)
                    else:
                        # 如果找到指定时间范围的视频，且是倒序排列，可以提前结束
                        has_more = False
                        break
                except Exception as e:
                    log.error(f"解析时间失败: {create_time_str}, 错误: {e}")
                    continue

            # 如果没有更多数据或已找到超过时间范围的数据，停止循环
            if not has_more:
                break

            tab.wait(2)

        except Exception as e:
            log.error(f"发生错误: {e}")
            break
    return videos


# 评论数据
def spider_douyin_comments(tab):
    """
    互动管理-评论管理
    """
    log.info("开始采集评论数据...")
    tab.get(url='https://creator.douyin.com/creator-micro/interactive/comment')
    tab.change_mode('s')

    video_items = get_recent_month_videos(tab=tab)
    print(video_items)





# 保存数据
def save_datas(table_id, datas):
    base_token = BASE_TOKEN  # 多维表格的基础token

    writer = FeishuBitableWriter(base_token, table_id)
    writer.add_records(datas)


def spider_douyin(page_douyin):
    try:
        global tab
        tab = page_douyin

        accounts_data = spider_douyin_account()
        # # 保存账号数据
        save_datas(table_id=TABLE_DY_ACCOUNTS, datas=accounts_data)

        notes_datas = spider_douyin_notes()
        # 保存帖子数据
        save_datas(table_id=TABLE_DY_NOTES, datas=notes_datas)

        final_data = {
            "数据平台": "抖音",
            "账号维度数据": accounts_data,
            "帖子维度数据": notes_datas,
        }
        log.info(final_data)
    except Exception as e:
        log.error(e)
        bot.send_card_alert(
            title="爬虫",
            task_name="爬虫计划任务运行「异常」时告警-新媒体数据-刘建强",
            run_script_name=f"{__file__}",
            exception_plan="爬虫-新媒体数据-刘建强",
            exception_app="抖音",
            error_message=f"任务失败，因为{e}",
            client_ip="10.30.40.150",
            at_all=False,
            at_user_ids=DEVELOPERS_ID_LIST
        )
        raise
    return final_data


if __name__ == '__main__':
    tab = Chromium().latest_tab
    spider_douyin(tab)
