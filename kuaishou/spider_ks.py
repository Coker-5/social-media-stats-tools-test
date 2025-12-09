from DrissionPage import Chromium
from tools.feishu_bitable_uploader import FeishuBitableWriter
from tools.logstar import get_logger

log = get_logger(__file__)
tab = Chromium().latest_tab


# 账号维度数据
def spider_douyin_account():
    # 首页
    log.info("开始采集账号维度数据...")
    tab.get(url='https://creator.douyin.com')
    tab.wait(6)

    # 粉丝数据
    log.info("正在采集粉丝维度数据...")
    parent_ele = tab.ele('.statics-kyUhqC')
    numbers = parent_ele.eles('.number-No6ev9')

    fans_num = numbers[1].text  # 粉丝
    likes_num = numbers[2].text  # 获赞


    # 浏览数据
    # 近七天
    parent_ele = tab.eles('.number-vDKr2F')
    play_count = parent_ele[0].text  # 播放量
    homepage_views = parent_ele[1].text  # 主页访问量
    likes = parent_ele[2].text  # 作品点赞
    shares = parent_ele[3].text  # 作品分享
    comments = parent_ele[4].text  # 作品评论
    followers = parent_ele[5].text  # 净增粉丝


    # 近三十天
    tab.ele("@role=combobox").click()
    option = tab.eles("@role=option")
    option[2].click()

    tab.wait(3)

    parent_ele = tab.eles('.number-vDKr2F')
    last_month_play_count = parent_ele[0].text  # 播放量
    last_month_homepage_views = parent_ele[1].text  # 主页访问量
    last_month_likes = parent_ele[2].text  # 作品点赞
    last_month_shares = parent_ele[3].text  # 作品分享
    last_month_comments = parent_ele[4].text  # 作品评论
    last_month_followers = parent_ele[5].text  # 净增粉丝


    accont_data = {
        "粉丝": int(fans_num),
        "获赞": int(likes_num),
        "近7天播放量": int(play_count),
        "近7天主页访问量": int(homepage_views),
        "近7天点赞": int(likes),
        "近7天分享": int(shares),
        "近7天评论": int(comments),
        "近7天净增粉丝": int(followers),

        "近30天播放量": int(last_month_play_count),
        "近30天主页访问量": int(last_month_homepage_views),
        "近30天点赞": int(last_month_likes),
        "近30天分享": int(last_month_shares),
        "近30天评论": int(last_month_comments),
        "近30天净增粉丝": int(last_month_followers),
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
            "x-secsdk-csrf-token": "00010000000138d4126a71745e49fddf2c9dd13eadb9e85cb78887b2274d3bc004450ebca88b187de7688ed0301f"
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
                max_cursor = notes_res["max_cursor"]
                has_more = notes_res['has_more']

                for index, note in enumerate(notes_res["items"]):

                    awesome_li = notes_res["aweme_list"][index]
                    is_private = awesome_li["status"]["is_private"]

                    if not is_private:
                        link = awesome_li["share_url"]  # 链接
                        description = note["description"]  # 帖子名称
                        create_time = note["create_time"] * 1000  # 发布时间
                        metrics = note["metrics"]
                        view_count = int(metrics["view_count"])  # 播放量
                        like_count = int(metrics["like_count"])  # 点赞数
                        comment_rate = int(metrics["comment_count"])  # 评论数
                        share_rate = int(float(metrics["share_rate"]))  # 分享数
                        favorite_count = int(metrics.get("favorite_count", 0))  # 收藏数
                        completion_rate_5s = str(round(float(metrics.get("completion_rate_5s", 0)) * 100, 2))  # 5s完播率
                        bounce_rate_2s = str(round(float(metrics.get("bounce_rate_2s", 0)) * 100, 1))  # 2s跳出率
                        avg_view_second = int(float(metrics.get("avg_view_second", 0)))  # 平均播放时长
                        completion_rate = str(round(float(metrics.get("completion_rate", 0)) * 100, 1))  # 完播率

                        note_data = {
                            "帖子名称": description,
                            "发布时间": create_time,
                            "播放量": view_count,
                            "点赞数": like_count,
                            "评论数": comment_rate,
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
                        log.info(note_data)
                        notes_datas.append(note_data)

        except Exception as e:
            log.error(e)
        finally:
            tab.wait(1.5)

    # for id in notes_ids:
    #     url = "https://creator.douyin.com/web/api/creator/item/mget"
    #     headers = {
    #         "accept": "*/*",
    #         "accept-language": "zh-CN,zh;q=0.9",
    #         "agw-js-conv": "str",
    #         "priority": "u=1, i",
    #         "referer": "https://creator.douyin.com/creator-micro/work-management/work-detail/7532684054816329018?enter_from=content",
    #         "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    #         "sec-ch-ua-mobile": "?0",
    #         "sec-ch-ua-platform": "\"macOS\"",
    #         "sec-fetch-dest": "empty",
    #         "sec-fetch-mode": "cors",
    #         "sec-fetch-site": "same-origin",
    #         "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    #         "x-secsdk-csrf-token": "0001000000011e10dc31421d2509a9c17e74e11ebcb7c6a138aaefae1c1fcb1fadcce8d892fc187df08a42db68f1"
    #     }
    #     params = {
    #         "ids": id,
    #         "fields": "metrics,review,play_info",
    #         "msToken": "L155D5OPyKIeRObrYc5y84UQHoxCDxM_A3LodB-T0jvXeduXZOqMg7ejHuW-hJp1hdIHz0kqmR5cFeqVKcweewMIjnnvuCL8rR-acTaWDy1Oace7KDjfrpexGk6z2P5tWf-43lFhCqqbkPPoWV8tFOmtnBg4lHPvg080z8vJf7PI3S9KF7KGQds=",
    #         "a_bogus": "d7sRhtWwOqQccpMGuCnKet2lKC6ANB8yieToWGfjeOwDcZ0OtZHpBNSdbooJsEEWDSBChCI7qEtlbdncszssZlnkKmkfSDhyxtAn9uXoZHksYPvh1rfECykFFXsaWmzwe556iAJl0UGL1nV-wHdm/Q/9CACKQQWhOZObk2YST9GgZu8I2pMsi/s27fjHRBngsJ6="
    #     }
    #     try:
    #         tab.get(url, headers=headers, params=params)
    #         if tab.response.ok:
    #             note_detail = tab.response.json()
    #             description = note_detail["items"][0]["description"] # 帖子名称
    #             create_time=note_detail["items"][0]["create_time"] # 发布时间
    #             view_count=note_detail["items"][0]["metrics"]["view_count"] # 播放量
    #             like_count=note_detail["items"][0]["metrics"]["like_count"] # 点赞数
    #             comment_rate=note_detail["items"][0]["metrics"]["comment_rate"] # 评论数
    #             share_rate=note_detail["items"][0]["metrics"]["share_rate"] # 分享数
    #             favorite_count=note_detail["items"][0]["metrics"]["favorite_count"] # 收藏数
    #             completion_rate_5s=note_detail["items"][0]["metrics"]["completion_rate_5s"] # 5s完播率
    #             bounce_rate_2s=note_detail["items"][0]["metrics"]["bounce_rate_2s"] # 2s跳出率
    #             avg_view_second=note_detail["items"][0]["metrics"]["avg_view_second"] # 平均播放时长
    #             completion_rate=note_detail["items"][0]["metrics"]["completion_rate"] # 完播率
    #
    #             note_data = {
    #                 "帖子名称": description,
    #                 "发布时间": datetime.datetime.fromtimestamp(int(create_time)).strftime('%Y-%m-%d %H:%M:%S'),
    #                 "播放量": view_count,
    #                 "点赞数": like_count,
    #                 "评论数": comment_rate,
    #                 "分享数": share_rate,
    #                 "收藏数": favorite_count,
    #                 "5秒完播率": completion_rate_5s,
    #                 "2秒跳出率": bounce_rate_2s,
    #                 "平均播放时长": avg_view_second,
    #                 "完播率": completion_rate
    #             }
    #             log.info(note_data)
    #             notes_datas.append(note_data)
    #
    #     except Exception as e:
    #         log.error(e)
    #     finally:
    #         tab.wait(2)
    return notes_datas


# 私信数据


# 评论数据


# 保存数据
def save_datas(table_id, datas):
    base_token = "YljGbJWV4a5KcVszswocsd0RnEe"  # 多维表格的基础token

    writer = FeishuBitableWriter(base_token, table_id)
    writer.add_records(datas)


def spider_douyin():
    accounts_data = spider_douyin_account()
    # 保存账号数据
    save_datas(table_id="tblEQv4wSINAwiO6", datas=accounts_data)

    notes_datas = spider_douyin_notes()
    # 保存帖子数据
    save_datas(table_id="tbllmZ7Ahf0RgLIQ", datas=notes_datas)

    final_data = {
        "数据平台": "抖音",
        "账号维度数据": accounts_data,
        "帖子维度数据": notes_datas,
    }
    log.info(final_data)
    return final_data


if __name__ == '__main__':
    spider_douyin()
