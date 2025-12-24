from DrissionPage import Chromium
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

    fans_num = numbers[1].text  # 粉丝
    likes_num = numbers[2].text  # 获赞

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
    if parent_ele and len(parent_ele) > 3:
        play_count = parent_ele[0].text  # 播放量
        homepage_views = parent_ele[1].text  # 主页访问量
        likes = parent_ele[2].text  # 作品点赞
        shares = parent_ele[3].text  # 作品分享
        comments = parent_ele[4].text  # 作品评论
        followers = parent_ele[5].text  # 净增粉丝

    # 昨天
    tab.ele("@role=combobox").click()
    option = tab.eles("@role=option")
    option[0].click()

    tab.wait(3)

    parent_ele = tab.eles('.number-vDKr2F')
    if parent_ele and len(parent_ele) > 3:
        yesterday_play_count = parent_ele[0].text  # 播放量
        yesterday_homepage_views = parent_ele[1].text  # 主页访问量
        yesterday_likes = parent_ele[2].text  # 作品点赞
        yesterday_shares = parent_ele[3].text  # 作品分享
        yesterday_comments = parent_ele[4].text  # 作品评论
        yesterday_followers = parent_ele[5].text  # 净增粉丝

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



# 评论数据
def spider_douyin_comments(tab):
    """
    互动管理-评论管理
    """
    log.info("开始采集评论数据...")
    tab.get(url='https://creator.douyin.com/creator-micro/interactive/comment')
    tab.wait(2)

    all_notes_items = []
    cursor = ""  # 初始游标为空
    has_more = True

    tab.change_mode('s')

    while has_more:
        params = {
            "cursor": cursor,
            "aid": "2906",
        }

        url = 'https://creator.douyin.com/aweme/v1/creator/item/list/'

        tab.get(url, params=params)
        res_data = tab.response.json()
        items = res_data["item_info_list"]
        for item in items:
            item_info = {
                "item_id": item.get("item_id"),  # 加密 ID
                "title": item.get("title")
            }
            all_notes_items.append(item_info)
            log.info(f"成功获取帖子: {item_info['title']} | ID: {item_info['item_id']}")

        # 更新分页参数
        has_more = res_data.get("has_more", False)
        cursor = res_data.get("cursor", "")

        tab.wait(1)  # 频率控制

    log.info(f"帖子列表采集完成，共获取 {len(all_notes_items)} 个帖子")

    # 后续遍历逻辑示例：
    # for note in all_notes:
    #     fetch_comments_by_item_id(note['item_id'])

    return all_notes_items




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
    # spider_douyin(tab)
    spider_douyin_comments(tab)