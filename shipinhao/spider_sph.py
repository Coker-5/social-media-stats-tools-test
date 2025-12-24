import os
from datetime import datetime

from shipinhao.parse_sph import parse_sph_notes
from tools.config_loader import BOT_WEBHOOK, DEVELOPERS_ID_LIST, BASE_TOKEN, TABLE_SPH_ACCOUNTS, TABLE_SPH_NOTES
from tools.data_clean import cleaning
from tools.feishu_bitable_uploader import FeishuBitableWriter
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from DrissionPage import Chromium
from pathlib import Path


BASE_DIR = Path(__file__).parent
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

    statics_dir = BASE_DIR / "statics"
    os.makedirs(statics_dir, exist_ok=True)

    file_name = f"{datetime.now().strftime('%Y_%m_%d_%H%M')}-视频号-帖子详情数据.csv"
    download_btn = container.ele(".filter-extra", timeout=2)
    mission = download_btn.click.to_download(save_path=str(statics_dir), rename=file_name)
    mission.wait(show=False)

    if mission:
        notes_datas = parse_sph_notes(file_path=str(statics_dir / file_name))

    return notes_datas


# 帖子数据
def save_datas(table_id, datas):
    writer = FeishuBitableWriter(BASE_TOKEN, table_id)
    writer.add_records(datas)


def spider_shipinhao(page_shipinhao):
    try:
        global tab
        tab = page_shipinhao

        accounts_data = spider_sph_accounts()
        # 保存账号数据
        save_datas(table_id=TABLE_SPH_ACCOUNTS, datas=accounts_data)

        notes_datas = spider_sph_notes()
        # 保存帖子数据
        save_datas(table_id=TABLE_SPH_NOTES, datas=notes_datas)

        final_data = {
            "数据平台": "视频号",
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
            exception_app="视频号",
            error_message=f"任务失败，因为{e}",
            client_ip="10.30.40.150",
            at_all=False,
            at_user_ids=DEVELOPERS_ID_LIST
        )
        raise



if __name__ == '__main__':
    tab = Chromium().latest_tab
    spider_shipinhao(page_shipinhao=tab)
