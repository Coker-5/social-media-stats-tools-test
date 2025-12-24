import json
import re
import time
from tools.config_loader import BOT_WEBHOOK, DEVELOPERS_ID_LIST, BASE_TOKEN, TABLE_KS_ACCOUNTS, TABLE_KS_NOTES
from tools.data_clean import cleaning
from tools.feishu_bitable_uploader import FeishuBitableWriter
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from DrissionPage import Chromium
from kuaishou.parse_ks import parse_ks_photo_list_data, parse_ks_photo_detail_data, format_note_data

bot = FeishuBot(BOT_WEBHOOK)
log = get_logger()
tab = None


# 账号维度数据
def spider_ks_accounts():
    global tab
    # 首页
    log.info("开始采集账号维度数据...")
    tab.get(url='https://cp.kuaishou.com/profile')
    tab.wait(6)

    # 粉丝数据
    fans_num = 0
    fans_element = tab.eles('.user-cnt__item', timeout=2)
    if fans_element:
        fans_num = fans_element[0].text
        fans_num = re.search(r'\d+', fans_num)[0]

    # 浏览数据
    # 近七天
    values = [div.text for div in tab.eles('.question-tips')]
    numbers = [item for item in values if '+' not in item]
    numbers = cleaning(numbers)
    play_count = numbers[0]  # 播放量
    likes = numbers[1]  # 点赞
    followers = numbers[2]  # 净增粉丝量
    completion_rate = numbers[3]  # 完播率
    comments = numbers[4]  # 评论
    shares = numbers[5]  # 分享

    # 近三十天
    filter = tab.ele(".pop_value el-popover__reference")
    filter.click()
    options = tab.eles(".option")
    options[1].click()
    tab.wait(3)

    values = [div.text for div in tab.eles('.question-tips')]
    numbers = [item for item in values if '+' not in item]
    numbers = cleaning(numbers)
    last_month_play_count = numbers[0]  # 播放量
    last_month_likes = numbers[1]  # 点赞
    last_month_followers = numbers[2]  # 净增粉丝量
    last_month_completion_rate = numbers[3]  # 完播率
    last_month_comments = numbers[4]  # 评论
    last_month_shares = numbers[5]  # 分享

    # 近九十天
    filter = tab.ele(".pop_value el-popover__reference")
    filter.click()
    options = tab.eles(".option")
    options[2].click()
    tab.wait(3)

    values = [div.text for div in tab.eles('.question-tips')]
    numbers = [item for item in values if '+' not in item]
    numbers = cleaning(numbers)
    last_3month_play_count = numbers[0]  # 播放量
    last_3month_likes = numbers[1]  # 点赞量
    last_3month_followers = numbers[2]  # 净增粉丝量
    last_3month_completion_rate = numbers[3]  # 完播率
    last_3month_comments = numbers[4]  # 评论量
    last_3month_shares = numbers[5]  # 分享量

    accont_data = {
        "粉丝": int(fans_num),

        "近7天播放量": int(play_count),
        "近7天点赞量": int(likes),
        "近7天净增粉丝量": int(followers),
        "近7天完播率": completion_rate,
        "近7天评论量": int(comments),
        "近7天分享量": int(shares),

        "近30天播放量": int(last_month_play_count),
        "近30天点赞量": int(last_month_likes),
        "近30天净增粉丝量": int(last_month_followers),
        "近30天完播率": last_month_completion_rate,
        "近30天评论量": int(last_month_comments),
        "近30天分享量": int(last_month_shares),

        "近90天播放量": int(last_3month_play_count),
        "近90天点赞量": int(last_3month_likes),
        "近90天净增粉丝量": int(last_3month_followers),
        "近90天完播率": last_3month_completion_rate,
        "近90天评论量": int(last_3month_comments),
        "近90天分享量": int(last_3month_shares),
    }

    log.info(accont_data)
    return accont_data


# 帖子维度数据
def spider_ks_notes():
    """
    采集快手创作者中心的帖子数据
    返回帖子维度数据列表
    """
    log.info("开始采集帖子维度数据...")
    tab.get(url='https://cp.kuaishou.com/statistics/article')
    tab.wait(2)
    tab.change_mode('s')

    notes_datas = []
    page_size = 10
    page_num = 0  # 快手接口从0开始
    total_pages = 1
    has_more = True

    # 请求头
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://cp.kuaishou.com",
        "Referer": "https://cp.kuaishou.com/statistics/article",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "returnSetRootDomainLoginUrl": "true",
        "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\""
    }

    url = "https://cp.kuaishou.com/rest/cp/creator/analysis/pc/photo/list"

    while has_more and page_num < 50:
        try:
            data = {
                "orderType": 2,
                "sortType": 1,
                "type": 0,
                "count": page_size,
                "page": page_num,
                "kuaishou.web.cp.api_ph": "61bd1b1d511a4e8fad735372b6fe731a6db2"
            }

            data_json = json.dumps(data, separators=(',', ':'))

            # 发送POST请求
            response = tab.post(
                url,
                headers=headers,
                data=data_json
            )

            if response.status_code == 200:
                result = response.json()
                photo_list = result.get("data", {}).get("photoList", {})
                total_count = photo_list.get("totalCount", 0)

                # 如果是第一页，计算总页数
                if page_num == 0 and total_count > 0:
                    total_pages = (total_count + page_size - 1) // page_size

                # 使用解析模块解析列表数据
                basic_infos = parse_ks_photo_list_data(result)

                # 处理当前页的数据
                for basic_info in basic_infos:
                    # 获取详细数据
                    try:
                        detail_data = {
                            "dataChangeType": 1,
                            "photoId": basic_info["photo_id"],
                            "tabType": 1,
                            "timeGranularity": 1,
                            "kuaishou.web.cp.api_ph": "61bd1b1d511a4e8fad735372b6fe731a6db2"
                        }
                        detail_url = "https://cp.kuaishou.com/rest/cp/creator/analysis/pc/photo/single/overview"

                        detail_response = tab.post(
                            detail_url,
                            headers=headers,
                            data=json.dumps(detail_data, separators=(',', ':'))
                        )

                        if detail_response.status_code == 200:
                            detail_result = detail_response.json()
                            # 使用解析模块解析详细数据
                            trend_data = parse_ks_photo_detail_data(detail_result)
                        else:
                            trend_data = {
                                "播放量": 0,
                                "平均播放时长": 0,
                                "封面点击率": 0,
                                "2s跳出率": 0,
                                "5s完播率": 0,
                                "完播率": 0
                            }

                        time.sleep(0.5)  # 避免请求过快

                    except Exception as e:
                        log.error(f"获取快手帖子 {basic_info['photo_id']} 详细数据失败: {str(e)}")
                        trend_data = {
                            "播放量": 0,
                            "平均播放时长": 0,
                            "封面点击率": 0,
                            "2s跳出率": 0,
                            "5s完播率": 0,
                            "完播率": 0
                        }

                    # 使用解析模块格式化数据
                    note_data = format_note_data(basic_info, trend_data)
                    if note_data:
                        log.info(note_data)
                        notes_datas.append(note_data)

                # 判断是否还有更多数据
                if len(basic_infos) < page_size or page_num >= total_pages - 1:
                    has_more = False
                else:
                    page_num += 1
                    time.sleep(1)  # 避免请求过快

            else:
                log.error(f"请求快手失败: {response.text}")
                raise ConnectionError(f"请求快手失败: {response.text}")

        except Exception as e:
            log.error(f"采集快手第{page_num + 1}页时出错: {str(e)}")
            raise

    return notes_datas


def save_datas(table_id, datas):
    writer = FeishuBitableWriter(BASE_TOKEN, table_id)
    writer.add_records(datas)


def spider_kuaishou(page_douyin):
    try:
        global tab
        tab = page_douyin

        accounts_data = spider_ks_accounts()
        # 保存账号数据
        save_datas(table_id=TABLE_KS_ACCOUNTS, datas=accounts_data)

        notes_datas = spider_ks_notes()
        # 保存帖子数据
        save_datas(table_id=TABLE_KS_NOTES, datas=notes_datas)

        final_data = {
            "数据平台": "快手",
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
            exception_app="快手",
            error_message=f"任务失败，因为{e}",
            client_ip="10.30.40.150",
            at_all=False,
            at_user_ids=DEVELOPERS_ID_LIST
        )
        raise


if __name__ == '__main__':
    tab = Chromium().latest_tab
    spider_kuaishou(tab)
