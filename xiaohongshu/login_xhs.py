import time
from DrissionPage import Chromium
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.config_loader import (BOT_WEBHOOK, USER_IDS)

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)


def login_xiaohongshu(page_xiaohongshu):
    try:
        tab = page_xiaohongshu
        tab.get("https://creator.xiaohongshu.com/new/home")
        tab.wait(2)

        login_btn = tab.ele(".login-box-container", timeout=2)
        if login_btn:
            log.warning("小红书创作者中心---登录已失效，请重新扫码登录")
            platform = "小红书"
            bot.send_card_alert(
                title="登录",
                title_color="yellow",
                task_name=f"监控告警-{platform}登录状态",
                exception_plan=f"爬虫-{platform}-新媒体数据采集",
                exception_app=f"{platform}",
                error_message=f"【{platform}】登录已失效，请尽快重新扫码登录",
                at_user_ids=[USER_IDS["罗粤"],USER_IDS["曾婉婷"]]
            )
            while True:
                log.info("登录状态检查中...")
                login_btn = tab.ele(".login-box-container")
                if not login_btn and tab.url == "https://creator.xiaohongshu.com/new/home":
                    break
                bot.send_card_alert(
                    title="登录",
                    title_color="yellow",
                    task_name=f"监控告警-{platform}登录状态",
                    exception_plan=f"爬虫-{platform}-新媒体数据采集",
                    exception_app=f"{platform}",
                    error_message=f"【{platform}】登录已失效，请尽快重新扫码登录",
                    at_user_ids=[USER_IDS["罗粤"],USER_IDS["曾婉婷"]]
                )
                time.sleep(60)
        log.info("小红书创作者中心---已成功登录")
    except Exception as e:
        log.error(e)
        raise


if __name__ == '__main__':
    tab = Chromium().latest_tab
    login_xiaohongshu(tab)
