import os
from datetime import datetime
from DrissionPage import Chromium
from tools.feishu_bitable_uploader import FeishuBitableWriter
from tools.logstar import get_logger
from tools.config_loader import (BASE_TOKEN, TABLE_XHS_NOTES, TABLE_XHS_ACCOUNTS, BOT_WEBHOOK, USER_IDS)
from tools.data_clean import cleaning
from tools.send_feishu import FeishuBot
from xiaohongshu.parse_xhs import parse_xhs_notes
import  warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
from pathlib import Path


BASE_DIR = Path(__file__).parent
log = get_logger()
tab = None
bot = FeishuBot(BOT_WEBHOOK)


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

            # 第一组数据（4个）
            imp_count = numbers[0]  # 曝光数
            play_count = numbers[1]  # 观看数
            cover_click_rate = numbers[2]  # 封面点击率
            full_view_rate = numbers[3]  # 视频完播率

            # 第二组数据（4个）
            likes = numbers[4]  # 点赞
            comments = numbers[5]  # 评论
            favorites = numbers[6]  # 收藏
            shares = numbers[7]  # 分享

            # 第三组数据（4个）
            rise_fans_count = numbers[8]  # 净涨粉
            new_followers = numbers[9]  # 新增关注
            cancel_followers = numbers[10]  # 取消关注
            homepage_views = numbers[11]  # 主页访客


            filter = tab.ele("text:近30日")
            filter.click()
            tab.wait(3)

            # 近三十天
            numbers = [elem.text for elem in tab.eles('.number')]
            numbers = cleaning(numbers)

            last_month_imp_count = numbers[0]  # 曝光数
            last_month_play_count = numbers[1]  # 观看数
            last_month_homepage_views = numbers[11]  # 主页访客
            last_month_likes = numbers[4]  # 点赞
            last_month_favorites = numbers[6]  # 收藏
            last_month_comments = numbers[5]  # 评论
            last_month_shares = numbers[7]  # 分享
            last_month_rise_fans_count = numbers[8]  # 净涨粉
            last_month_new_followers = numbers[9]  # 新增关注
            last_month_cancel_followers = numbers[10]  # 取消关注
            last_month_cover_click_rate = numbers[2]  # 封面点击率
            last_month_full_view_rate = numbers[3]  # 视频完播率

            accont_data = {
                "粉丝": int(fans_num),
                "获赞": int(likes_num),
                "近7天曝光": int(imp_count),
                "近7天观看": int(play_count),
                "近7天封面点击率": cover_click_rate,
                "近7天视频完播率": full_view_rate ,
                "近7天点赞": int(likes),
                "近7天评论": int(comments),
                "近7天收藏": int(favorites),
                "近7天分享": int(shares),
                "近7天净涨粉": int(rise_fans_count),
                "近7天新增关注": int(new_followers),
                "近7天取消关注": int(cancel_followers),
                "近7天主页访客": int(homepage_views),

                "近30天曝光": int(last_month_imp_count),
                "近30天观看": int(last_month_play_count),
                "近30天封面点击率": last_month_cover_click_rate,
                "近30天视频完播率": last_month_full_view_rate,
                "近30天主页访客": int(last_month_homepage_views),
                "近30天点赞": int(last_month_likes),
                "近30天收藏": int(last_month_favorites),
                "近30天分享": int(last_month_shares),
                "近30天评论": int(last_month_comments),
                "近30天净涨粉": int(last_month_rise_fans_count),
                "近30天新增关注": int(last_month_new_followers),
                "近30天取消关注": int(last_month_cancel_followers)
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

    statics_dir = BASE_DIR / "statics"
    os.makedirs(statics_dir, exist_ok=True)

    file_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M')}-小红书-帖子详情数据.xlsx"
    download_btn = tab.ele("text:导出数据")
    mission = download_btn.click.to_download(save_path=str(statics_dir), rename=file_name)
    mission.wait(show=False)

    if mission:
        notes_datas = parse_xhs_notes(file_path=str(statics_dir / file_name))

    return notes_datas


# 保存数据
def save_datas(table_id, datas):
    base_token = BASE_TOKEN  # 多维表格的基础token

    writer = FeishuBitableWriter(base_token, table_id)
    writer.add_records(datas)


def spider_xiaohongshu(page_xiaohongshu):
    try:
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
    except Exception as e:
        log.error(e)
        bot.send_card_alert(
            title="爬虫",
            task_name="爬虫计划任务运行「异常」时告警-新媒体数据-刘建强",
            run_script_name=f"{__file__}",
            exception_plan="小红书-新媒体数据-刘建强",
            exception_app="小红书",
            error_message=f"任务失败，因为{e}",
            client_ip="10.30.40.150",
            at_all=False,
            at_user_ids=[USER_IDS["刘建强"]]  # 替换为实际的用户ID
        )
        raise
    return final_data


if __name__ == '__main__':
    tab = Chromium().latest_tab
    spider_xiaohongshu(tab)
