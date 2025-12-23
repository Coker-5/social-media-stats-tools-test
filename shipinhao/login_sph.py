import time
from DrissionPage import Chromium, ChromiumPage
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.config_loader import BOT_WEBHOOK, USER_IDS

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)


def login_shipinhgao(page_shipinhgao, alert_interval = 300):
    """登录视频号创作者中心"""

    def send_login_alert(last_alert_time: float, platform: str) -> float:
        """发送登录告警，返回发送时间戳"""
        bot.send_card_alert(
            title="登录",
            title_color="yellow",
            task_name=f"监控告警-{platform}登录状态",
            exception_plan=f"爬虫-{platform}-新媒体数据采集",
            exception_app=platform,
            error_message=f"【{platform}】登录已失效，请尽快重新扫码登录",
            at_user_ids=[USER_IDS["罗粤"], USER_IDS["曾婉婷"]]
        )
        log.info("发送登录提醒")
        return time.time()

    try:
        tab = page_shipinhgao
        platform = "视频号"

        # 访问页面
        tab.get('https://channels.weixin.qq.com/platform')
        tab.wait.doc_loaded()

        # 初始化告警时间
        last_alert_time = 0

        # 检查初始登录状态
        login_btn = tab.ele(".login-content", timeout=2)
        is_login_page = "login" in tab.url.lower()

        if login_btn and is_login_page:
            log.warning(f"{platform}创作者中心---登录已失效，请重新扫码登录")
            last_alert_time = send_login_alert(last_alert_time, platform=platform)

            # 无限循环等待登录
            while True:
                # 检查是否需要重新发送告警
                current_time = time.time()
                if current_time - last_alert_time >= alert_interval:
                    last_alert_time = send_login_alert(last_alert_time, platform=platform)

                # 检查登录状态
                login_btn = tab.ele(".login-content", timeout=2)
                is_login_page = "login" in tab.url.lower()

                # 如果登录成功
                if not login_btn and not is_login_page:
                    log.info(f"{platform}创作者中心---已成功登录")
                    break

                # 每30秒检查一次登录状态
                log.info(f"{platform}登录状态检查中...")
                time.sleep(30)
        else:
            log.info(f"{platform}创作者中心---已成功登录")

    except Exception as e:
        log.error(f"登录视频号时发生错误: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    tab = Chromium().latest_tab
    login_shipinhgao(tab)  # 每5分钟发送一次告警
