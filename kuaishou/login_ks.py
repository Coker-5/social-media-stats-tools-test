import time
from DrissionPage import Chromium
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.config_loader import (BOT_WEBHOOK, OPERATIONS_ID_LIST)

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)


def login_kuaishou(page_kuaishou):
    try:
        tab = page_kuaishou
        platform = "快手"
        tab.get('https://cp.kuaishou.com/profile')
        tab.wait(2)

        login_btn = tab.ele(".login", timeout=2)
        if login_btn:
            log.warning("快手创作者中心---登录已失效，请重新扫码登录")
            bot.send_card_alert(
                title="登录",
                title_color="yellow",
                task_name=f"监控告警-{platform}登录状态",
                exception_plan=f"爬虫-{platform}-新媒体数据采集",
                exception_app=f"{platform}",
                error_message=f"【{platform}】登录已失效，请尽快重新扫码登录",
                at_user_ids=OPERATIONS_ID_LIST
            )
            while True:
                log.info("登录状态检查中...")
                login_btn = tab.ele(".login")
                if not login_btn and "login" not in tab.url:
                    break
                bot.send_card_alert(
                    title="登录",
                    title_color="yellow",
                    task_name=f"监控告警-{platform}登录状态",
                    exception_plan=f"爬虫-{platform}-新媒体数据采集",
                    exception_app=f"{platform}",
                    error_message=f"【{platform}】登录已失效，请尽快重新扫码登录",
                    at_user_ids=OPERATIONS_ID_LIST
                )
                log.info("登录状态检查中...")
                time.sleep(60)
        log.info("快手创作者中心---已成功登录")
    except Exception as e:
        log.error(e)
        raise


if __name__ == '__main__':
    tab = Chromium().latest_tab
    login_kuaishou(tab)
