import time
from DrissionPage import Chromium
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.config_loader import BOT_WEBHOOK, OPERATIONS_ID_LIST

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)


def is_shipinhgao_login(page_shipinhgao):
    """
    检查视频号是否已登录
    :param page_shipinhgao: 浏览器标签页对象
    :return: True表示已登录，False表示未登录
    """
    try:
        # 检查登录组件是否存在
        login_btn = page_shipinhgao.ele(".login-content", timeout=2)

        # 检查URL是否包含登录页面标识
        is_login_page = "login" in page_shipinhgao.url.lower()

        # 如果没有登录组件且不在登录页面，则表示已登录
        if not login_btn and not is_login_page:
            return True
        else:
            return False

    except Exception as e:
        log.warning(f"检查视频号登录状态时发生错误: {e}")
        return False


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
    log.info(f"发送提醒: {platform} {reason}")
    return time.time()


def login_shipinhgao(page_shipinhgao, alert_interval=180, timeout_limit=1200):
    """
    登录视频号创作者中心
    :param page_shipinhgao: 浏览器标签页对象
    :param alert_interval: 告警频率间隔（秒），默认3分钟
    :param timeout_limit: 最大等待扫码时间（秒），默认20分钟
    """
    try:
        tab = page_shipinhgao
        platform = "视频号"

        # 访问视频号创作者中心
        tab.get('https://channels.weixin.qq.com/platform')
        tab.wait.doc_loaded()

        start_wait_time = time.time()
        last_alert_time = 0

        # 检查初始登录状态
        if is_shipinhgao_login(tab):
            log.info(f"{platform}创作者中心---已成功登录")
            return
        else:
            log.warning(f"{platform}创作者中心---登录已失效，请重新扫码登录")
            last_alert_time = send_login_alert(platform)

        # 等待登录循环
        while True:
            if is_shipinhgao_login(tab):
                log.info(f"{platform}创作者中心---已成功登录")
                break

            current_time = time.time()
            # 检查是否超时
            if current_time - start_wait_time > timeout_limit:
                error_msg = f"{platform}登录已超时，请联系管理员"
                log.error(error_msg)
                send_login_alert(platform, reason=f"登录已超时，请联系管理员")
                break

            # 控制告警频率
            if current_time - last_alert_time >= alert_interval:
                last_alert_time = send_login_alert(platform)

            # 轮询间隔
            elapsed_time = int(current_time - start_wait_time)
            log.info(f"{platform}正在等待扫码，已耗时 {elapsed_time}s...")
            time.sleep(30)

    except Exception as e:
        log.error(f"登录视频号时发生错误: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    browser = Chromium()
    tab = browser.latest_tab
    login_shipinhgao(tab)