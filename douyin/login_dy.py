import time
from DrissionPage import Chromium
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.config_loader import (BOT_WEBHOOK, OPERATIONS_ID_LIST)

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)


def is_douyin_login(page_douyin):
    """
    检查抖音是否已登录
    :param page_douyin: 浏览器标签页对象
    :param target_url: 登录成功后的目标URL
    :return: True表示已登录，False表示未登录
    """
    target_url = "https://creator.douyin.com/creator-micro/home"
    try:
        login_btn = page_douyin.ele(".flat_container-FFKCgg", timeout=2)

        url_matches = page_douyin.url == target_url

        if not login_btn and url_matches:
            return True
        else:
            return False

    except Exception as e:
        log.warning(f"检查登录状态时发生错误: {e}")
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


def login_douyin(page_douyin, alert_interval=180, timeout_limit=1200):
    """
    登录抖音创作者中心
    :param page_douyin: 浏览器标签页对象
    :param alert_interval: 告警频率间隔（秒），默认3分钟
    :param timeout_limit: 最大等待扫码时间（秒），默认20分钟
    """
    try:
        tab = page_douyin
        platform = "抖音"

        tab.get('https://creator.douyin.com/')
        tab.wait(2)

        start_wait_time = time.time()
        last_alert_time = 0

        # 检查初始登录状态
        if is_douyin_login(tab):
            log.info(f"{platform}创作者中心---已成功登录")
            return
        else:
            log.warning(f"{platform}创作者中心---登录已失效，请重新扫码登录")
            last_alert_time = send_login_alert(platform)

        # 等待登录循环
        while True:
            if is_douyin_login(tab):
                log.info(f"{platform}创作者中心---已成功登录")
                break

            current_time = time.time()
            if current_time - start_wait_time > timeout_limit:
                error_msg = f"{platform}登录已超时，请联系管理员"
                log.error(error_msg)
                send_login_alert(platform, reason=f"登录已超时，请联系管理员")
                break

            if current_time - last_alert_time >= alert_interval:
                last_alert_time = send_login_alert(platform)

            # 轮询间隔
            elapsed_time = int(current_time - start_wait_time)
            log.info(f"{platform}正在等待扫码，已耗时 {elapsed_time}s...")
            time.sleep(30)

    except Exception as e:
        log.error(f"登录时发生错误: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    tab = Chromium().latest_tab
    login_douyin(tab)