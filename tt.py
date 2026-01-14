import time
import sentry_sdk
from kuaishou.login_ks import login_kuaishou
from kuaishou.spider_ks import spider_ks_accounts, spider_ks_notes
from shipinhao.login_sph import login_shipinhgao
from tools.logstar import get_logger
from douyin.login_dy import login_douyin
from douyin.spider_dy import spider_douyin, spider_douyin_account, spider_douyin_notes
from tools.send_feishu import FeishuBot
from xiaohongshu.login_xhs import login_xiaohongshu
from DrissionPage import Chromium
from shipinhao.login_sph import login_shipinhgao
from shipinhao.spider_sph import spider_sph_accounts, save_datas, spider_sph_notes
from tools.config_loader import TABLE_SPH_ACCOUNTS, TABLE_SPH_NOTES, TABLE_DY_NOTES, TABLE_DY_ACCOUNTS, \
    TABLE_XHS_ACCOUNTS, TABLE_XHS_NOTES, TABLE_KS_NOTES, TABLE_KS_ACCOUNTS
from tools.config_loader import (START_TIME, BOT_WEBHOOK, DEVELOPERS_ID_LIST)
from tools.sentry_config import init_sentry
from xiaohongshu.spider_xhs import spider_xhs_accounts, spider_xhs_notes

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)
init_sentry()

# from DrissionPage import ChromiumOptions
# co = ChromiumOptions()
# browser_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
# co.set_browser_path(browser_path)

browser = Chromium()


def douyin():
    global browser

    page_douyin = browser.new_tab()

    login_statu = login_douyin(page_douyin, alert_interval=480, timeout_limit=7200)
    if login_statu:
        accounts_data = spider_douyin_account()
        # 保存账号数据
        save_datas(table_id=TABLE_DY_ACCOUNTS, datas=accounts_data)

        notes_datas = spider_douyin_notes()
        # 保存帖子数据
        save_datas(table_id=TABLE_DY_NOTES, datas=notes_datas)

def xiaohongshu():
    global browser

    page_xiaohongshu = browser.new_tab()

    login_statu = login_xiaohongshu(page_xiaohongshu, alert_interval=480, timeout_limit=7200)
    if login_statu:
        accounts_data = spider_xhs_accounts()
        # 保存账号数据
        save_datas(table_id=TABLE_XHS_ACCOUNTS, datas=accounts_data)

        notes_datas = spider_xhs_notes()
        # 保存帖子数据
        save_datas(table_id=TABLE_XHS_NOTES, datas=notes_datas)

def kuaishou():
    global browser

    page_kuaishou = browser.new_tab()

    login_statu = login_kuaishou(page_kuaishou, alert_interval=480, timeout_limit=7200)
    if login_statu:
        accounts_data = spider_ks_accounts()
        # 保存账号数据
        save_datas(table_id=TABLE_KS_ACCOUNTS, datas=accounts_data)

        notes_datas = spider_ks_notes()
        # 保存帖子数据
        save_datas(table_id=TABLE_KS_NOTES, datas=notes_datas)

def shipinhao():
    global browser

    page_shipinhao = browser.new_tab()

    login_statu = login_shipinhgao(page_shipinhao, alert_interval=480, timeout_limit=7200)
    if login_statu:

        accounts_data = spider_sph_accounts()
        # 保存账号数据
        save_datas(table_id=TABLE_SPH_ACCOUNTS, datas=accounts_data)

        notes_datas = spider_sph_notes()
        # 保存帖子数据
        save_datas(table_id=TABLE_SPH_NOTES, datas=notes_datas)





if __name__ == '__main__':
    shipinhao()
