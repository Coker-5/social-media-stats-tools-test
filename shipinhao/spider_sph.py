import json
import os
import re
import time
from datetime import datetime

from shipinhao.parse_sph import parse_sph_notes
from tools.config_loader import BOT_WEBHOOK, USER_IDS, BASE_TOKEN, TABLE_KS_ACCOUNTS, TABLE_KS_NOTES
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
def spider_sph_accounts():
    global tab
    # 首页
    log.info("开始采集账号维度数据...")
    tab.get(url='https://channels.weixin.qq.com/platform/')
    tab.wait(6)

    # 粉丝数据
    fans_num = tab.ele('.finder-info-num', timeout=2).text
    fans_num = fans_num if fans_num else 0


    # 浏览数据
    data_elements = tab.eles('.data')
    values = [ele.text.strip() for ele in data_elements]
    numbers = cleaning(values)
    followers = numbers[0]  # 净增关注
    play_count = numbers[1]  # 新增播放
    like_counts = numbers[2]  # 新增点赞
    comments = numbers[3]  # 新增评论


    accont_data = {
        "粉丝": int(fans_num),

        "净增关注": int(followers),
        "新增播放": int(play_count),
        "新增点赞": int(like_counts),
        "新增评论": int(comments),
    }

    log.info(accont_data)
    return accont_data


def spider_sph_notes():
    # 数据中心-视频数据
    log.info("开始采集帖子维度数据...")
    tab.get(url='https://channels.weixin.qq.com/platform/statistic/post')
    tab.wait(6)

    container = tab.ele('.wujie_iframe', timeout=2).shadow_root
    single_mv_btn = container.ele('.weui-desktop-tab__nav', timeout=2)
    if single_mv_btn:
        single_mv_btn.click()
        tab.wait(2)
    last_month_btn = container.ele("text:近30天", timeout=2)
    if last_month_btn:
        last_month_btn.click()
        tab.wait(2)
    tab.wait(2)


    notes_datas = []

    os.makedirs("statics", exist_ok=True)
    file_name = f"{datetime.now().strftime('%Y_%m_%d_%H:%M')}-视频号-帖子详情数据"
    download_btn = container.ele(".filter-extra", timeout=2)
    mission = download_btn.click.to_download(save_path='./statics/', rename=file_name)
    mission.wait(show=False)

    if mission:
        notes_datas = parse_sph_notes(file_path="./statics/" + file_name +".csv")

    return notes_datas



if __name__ == '__main__':
    tab = Chromium().latest_tab
    # spider_sph_accounts()
    spider_sph_notes()
