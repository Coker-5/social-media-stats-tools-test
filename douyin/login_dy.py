import time
from DrissionPage import Chromium
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
import config

log = get_logger()
tab = Chromium().latest_tab
bot = FeishuBot(config.BOT_WEBHOOK)

def login_douyin():

    tab.get('https://creator.douyin.com/')
    tab.wait(2)

    login_btn = tab.ele(".flat_container-FFKCgg",timeout=2)
    if login_btn:
        log.warning("抖音创作者中心---登录已失效，请重新扫码登录")
        bot.send_text(text="【 抖音创作者中心 】登录已失效，请重新扫码登录",at_all=True)
        while True:
            log.info("登录状态检查中...")
            login_btn = tab.ele(".flat_container-FFKCgg")
            if not login_btn and tab.url == "https://creator.douyin.com/creator-micro/home":
                break
            bot.send_text(text="【 抖音创作者中心 】登录已失效，请重新扫码登录", at_all=True)
            time.sleep(20)
    log.info("抖音创作者中心---已成功登录")



if __name__ == '__main__':
    login_douyin()