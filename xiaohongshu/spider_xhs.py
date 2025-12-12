import os
from datetime import datetime
from DrissionPage import Chromium
from tools.feishu_bitable_uploader import FeishuBitableWriter
from tools.logstar import get_logger
from tools.config_loader import (BASE_TOKEN, TABLE_XHS_NOTES, TABLE_XHS_ACCOUNTS)
from tools.data_clean import cleaning
from xiaohongshu.parse_xhs import read_notes_from_excel
import  warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

log = get_logger()
tab = None


# 账号维度数据
def spider_xhs_accounts():
    # 首页
    log.info("开始采集账号维度数据...")
    tab.get(url='https://creator.xiaohongshu.com/new/home')
    tab.wait(6)

    fans_num = 0
    likes_num = 0

    # 小红书主页偶尔会返回空html，增加重试机制次
    try_count = 0
    while True:
        fans_element = tab.ele('text=粉丝数', timeout=2)
        if try_count > 5:
            log.error("小红书主页访问错误！！！")
            break
        if fans_element:
            if fans_element:
                # 获取前一个兄弟元素（数值元素）
                fans_num = fans_element.prev().text

            # 找到"获赞与收藏"前面的数值
            likes_element = tab.ele('text=获赞与收藏', timeout=2)
            if likes_element:
                likes_num = likes_element.prev().text

            tab.wait(3)

            # 浏览数据
            # 近七天
            numbers = [elem.text for elem in tab.eles('.number')]
            numbers = cleaning(numbers)
            play_count = numbers[0]  # 观看
            play_time = numbers[1]  # 观看总时长
            homepage_views = numbers[2]  # 主页访客
            likes = numbers[3]  # 点赞
            favorites = numbers[4]  # 收藏
            comments = numbers[5]  # 评论
            bullet = numbers[6]  # 弹幕
            followers = numbers[7]  # 笔记涨粉
            shares = numbers[8]  # 分享

            filter = tab.ele(".filter")
            filter.ele(".btn").click()
            tab.wait(3)

            # 近三十天
            numbers = [elem.text for elem in tab.eles('.number')]
            numbers = cleaning(numbers)
            last_month_play_count = numbers[0]  # 观看
            last_month_play_time = numbers[1]  # 观看总时长
            last_month_homepage_views = numbers[2]  # 主页访客
            last_month_likes = numbers[3]  # 点赞
            last_month_favorites = numbers[4]  # 收藏
            last_month_comments = numbers[5]  # 评论
            last_month_bullet = numbers[6]  # 弹幕
            last_month_followers = numbers[7]  # 笔记涨粉
            last_month_shares = numbers[8]  # 分享

            accont_data = {
                "粉丝": int(fans_num),
                "获赞": int(likes_num),
                "近7天观看": int(play_count),
                "近7天观看总时长": float(play_time),
                "近7天主页访客": int(homepage_views),
                "近7天点赞": int(likes),
                "近7天收藏": int(favorites),
                "近7天分享": int(shares),
                "近7天评论": int(comments),
                "近7天弹幕": int(bullet),
                "近7天笔记涨粉": int(followers),

                "近30天观看": int(last_month_play_count),
                "近30天观看总时长": float(last_month_play_time),
                "近30天主页访客": int(last_month_homepage_views),
                "近30天点赞": int(last_month_likes),
                "近30天收藏": int(last_month_favorites),
                "近30天分享": int(last_month_shares),
                "近30天评论": int(last_month_comments),
                "近30天弹幕": int(last_month_bullet),
                "近30天笔记涨粉": int(last_month_followers),
            }

            log.info(accont_data)
            return accont_data
        else:
            tab.refresh()
            log.info(f"小红书重试第{try_count + 1}次")
            try_count += 1
            tab.wait(5)


# 帖子维度数据
def spider_xhs_notes():
    # 数据看板-内容分析-笔记数据
    log.info("开始采集帖子维度数据...")
    tab.get(url='https://creator.xiaohongshu.com/statistics/data-analysis')
    tab.wait(2)

    notes_datas = []

    os.makedirs("statics", exist_ok=True)
    file_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M')}-小红书-帖子详情数据.xlsx"
    download_btn = tab.ele("text:导出数据")
    mission = download_btn.click.to_download(save_path='./statics/', rename=file_name)
    mission.wait(show=False)

    if mission:
        notes_datas = read_notes_from_excel(file_path="./statics/" + file_name)

    return notes_datas


# 保存数据
def save_datas(table_id, datas):
    base_token = BASE_TOKEN  # 多维表格的基础token

    writer = FeishuBitableWriter(base_token, table_id)
    writer.add_records(datas)


def spider_xiaohongshu(page_xiaohongshu):
    global tab
    tab = page_xiaohongshu
    accounts_data = spider_xhs_accounts()
    # 保存账号数据
    save_datas(table_id=TABLE_XHS_ACCOUNTS, datas=accounts_data)

    notes_datas = spider_xhs_notes()
    # 保存帖子数据
    save_datas(table_id=TABLE_XHS_NOTES, datas=notes_datas)

    final_data = {
        "数据平台": "小红书",
        "账号维度数据": accounts_data,
        "帖子维度数据": notes_datas,
    }
    log.info(final_data)
    return final_data


if __name__ == '__main__':
    tab = Chromium().latest_tab
    spider_xiaohongshu(tab)
