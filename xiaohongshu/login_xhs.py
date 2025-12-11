import time
from DrissionPage import Chromium
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.config_loader import (BOT_WEBHOOK)

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)


def login_xiaohongshu(page_xiaohongshu):
    tab = page_xiaohongshu
    tab.get("https://creator.xiaohongshu.com/new/home")
    tab.wait(2)

    login_btn = tab.ele(".login-box-container", timeout=2)
    if login_btn:
        log.warning("小红书创作者中心---登录已失效，请重新扫码登录")
        bot.send_text(text="【 小红书创作者中心 】登录已失效，请重新扫码登录", at_all=True)
        while True:
            log.info("登录状态检查中...")
            login_btn = tab.ele(".login-box-container")
            if not login_btn and tab.url == "https://creator.xiaohongshu.com/new/home":
                break
            bot.send_text(text="【 小红书创作者中心 】登录已失效，请重新扫码登录", at_all=True)
            time.sleep(30)
    log.info("小红书创作者中心---已成功登录")


if __name__ == '__main__':
    tab = Chromium().latest_tab
    login_xiaohongshu(tab)
