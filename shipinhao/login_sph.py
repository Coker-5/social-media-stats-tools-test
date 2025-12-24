import time
from DrissionPage import Chromium
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.config_loader import BOT_WEBHOOK, OPERATIONS_ID_LIST

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)

def login_shipinhgao(page_shipinhgao, alert_interval=180, timeout_limit=1200):
    """登录视频号创作者中心"""

    def send_login_alert(platform: str, reason: str = "登录已失效") -> float:
        """发送登录告警"""
        bot.send_card_alert(
            title="登录",
            title_color="yellow",
            task_name=f"监控告警-{platform}登录状态",
            exception_plan=f"爬虫-{platform}-新媒体数据采集",
            exception_app=platform,
            error_message=f"【{platform}】{reason}，请尽快重新扫码登录",
            at_user_ids=OPERATIONS_ID_LIST
        )
        log.info(f"发送登录提醒: {reason}")
        return time.time()

    try:
        tab = page_shipinhgao
        platform = "视频号"

        tab.get('https://channels.weixin.qq.com/platform')
        tab.wait.doc_loaded()

        # 记录进入登录流程的初始时间
        start_wait_time = time.time()
        last_alert_time = 0

        while True:
            # 检查登录状态
            login_btn = tab.ele(".login-content", timeout=2)
            is_login_page = "login" in tab.url.lower()

            # 1. 如果检测不到登录组件且不在登录URL，说明登录成功
            if not login_btn and not is_login_page:
                log.info(f"{platform}创作者中心---已成功登录")
                break

            # 2. 检查是否发生总超时（20分钟）
            current_time = time.time()
            if current_time - start_wait_time > timeout_limit:
                error_msg = f"{platform}登录已超时，请联系管理员"
                log.error(error_msg)
                send_login_alert(platform, reason=f"登录已超时，请联系管理员")
                break

            # 3. 检查是否需要发送/重发告警（每3分钟）
            if current_time - last_alert_time >= alert_interval:
                log.warning(f"{platform}等待扫码中...")
                last_alert_time = send_login_alert(platform)

            # 4. 轮询间隔
            log.info(f"{platform}正在等待扫码，已耗时 {int(current_time - start_wait_time)}s...")
            time.sleep(30)

    except Exception as e:
        log.error(f"登录视频号时发生错误: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    # 示例调用
    browser = Chromium()
    tab = browser.latest_tab
    login_shipinhgao(tab)