import io
import time
from DrissionPage import Chromium
from PIL import Image

from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.config_loader import (BOT_WEBHOOK, OPERATIONS_ID_LIST, APP_ID, APP_SECRET)

log = get_logger()
# 传入 APP_ID 和 APP_SECRET 才能支持飞书图片上传功能
bot = FeishuBot(BOT_WEBHOOK, APP_ID, APP_SECRET)


def get_login_qrcode(tab, platform, target_size=(180, 180)):
    """
    获取并处理二维码：处理小红书点击切换、去灰、二值化处理
    """
    try:
        if tab.ele(".css-wemwzq", timeout=3):
            tab.ele(".css-wemwzq").click()
            tab.wait(1)

        tab.wait.ele_displayed(".login-box-container", timeout=5)
        login_content = tab.ele(".login-box-container")
        qrcode_img = login_content.eles("tag:img")[1]

        if qrcode_img:
            qrcode_bytes = qrcode_img.src(timeout=5, base64_to_bytes=True)
            if not qrcode_bytes: return None

            try:
                with Image.open(io.BytesIO(qrcode_bytes)) as img:
                    # 第一步：转为 RGBA 处理透明背景
                    img = img.convert("RGBA")

                    # 第二步：白底填充，去除灰色背景
                    canvas = Image.new("RGBA", img.size, (255, 255, 255, 255))
                    canvas.paste(img, (0, 0), img)

                    # 第三步：二值化处理（亮度低于200设为纯黑，否则纯白）
                    gray = canvas.convert("L")
                    bw_img = gray.point(lambda x: 0 if x < 200 else 255, '1')

                    # 第四步：调整尺寸并转回 RGB
                    final_img = bw_img.convert("RGB")
                    final_img = final_img.resize(target_size, Image.Resampling.LANCZOS)

                    # 返回字节流
                    buf = io.BytesIO()
                    final_img.save(buf, format='PNG')
                    return buf.getvalue()

            except Exception as e:
                log.warning(f"图片像素处理失败: {e}")
                return qrcode_bytes
    except Exception as e:
        log.error(f"获取二维码失败: {e}")
        return None


def is_xiaohongshu_login(page_xiaohongshu):
    """
    检查小红书是否已登录
    """
    target_url = "https://creator.xiaohongshu.com/new/home"
    try:
        # 检查登录容器是否存在
        login_container = page_xiaohongshu.ele(".login-box-container", timeout=2)
        # 检查 URL 是否包含创作者中心核心路径
        url_matched = target_url in page_xiaohongshu.url

        # 如果没有登录框且 URL 匹配，则视为已登录
        if not login_container and url_matched:
            return True
        else:
            return False
    except Exception as e:
        log.warning(f"检查登录状态时发生错误: {e}")
        return False


def send_login_card(platform: str, statu: bool, reason: str = "", screenshot_bytes: bytes = None):
    """
    发送登录通知卡片（与视频号标准对齐）
    """
    if statu:
        bot.send_card_success(
            title="登录成功",
            task_name=f"爬虫-{platform}-新媒体数据采集",
            platform=platform,
            success_message=f"【{platform}】登录成功 "
        )
    else:
        if screenshot_bytes:
            bot.send_card_alert(
                title="登录",
                title_color="yellow",
                task_name=f"监控告警-{platform}登录状态",
                run_script_name=__name__,
                exception_plan=f"爬虫-{platform}-新媒体数据采集",
                exception_app=platform,
                error_message=f"【{platform}】{reason}，请尽快重新扫码登录。",
                screenshot_bytes=screenshot_bytes,
                screenshot_text=f"{platform}最新登录二维码：",
                at_user_ids=OPERATIONS_ID_LIST
            )
        else:
            bot.send_card_alert(
                title="登录告警",
                title_color="yellow",
                task_name=f"监控告警-{platform}登录状态",
                exception_plan=f"爬虫-{platform}-新媒体数据采集",
                exception_app=platform,
                error_message=f"【{platform}】{reason}",
                at_user_ids=OPERATIONS_ID_LIST
            )
        log.info(f"发送提醒: {platform} {reason}")

    return time.time()


def login_xiaohongshu(page_xiaohongshu, alert_interval=300, timeout_limit=1200):
    """
    登录小红书创作者中心
    :param page_xiaohongshu: 浏览器标签页对象
    :param alert_interval: 告警频率间隔（秒），默认5分钟
    :param timeout_limit: 最大等待扫码时间（秒），默认20分钟
    """
    try:
        tab = page_xiaohongshu
        platform = "小红书"

        tab.get("https://creator.xiaohongshu.com/new/home")
        tab.wait(3)

        start_wait_time = time.time()
        last_alert_time = 0

        # 1. 检查初始登录状态
        if is_xiaohongshu_login(tab):
            log.info(f"{platform}创作者中心---已成功登录")
            return True
        else:
            log.warning(f"{platform}创作者中心---登录已失效，请重新扫码登录")
            # 初始失效提醒
            qr_code_data = get_login_qrcode(tab, platform)
            last_alert_time = send_login_card(platform, statu=False, reason="登录已失效",
                                              screenshot_bytes=qr_code_data)

        # 2. 等待登录循环
        while True:
            current_time = time.time()

            # 检查扫码成功状态
            if is_xiaohongshu_login(tab):
                log.info(f"{platform}创作者中心---已成功登录")
                send_login_card(platform=platform, statu=True)
                return True

            # 超时退出
            if current_time - start_wait_time > timeout_limit:
                error_msg = f"{platform}登录已超时，请联系管理员"
                log.error(error_msg)
                send_login_card(platform, statu=False, reason=error_msg)
                return False

            # 定时刷新并重新推送二维码（防止过期）
            if current_time - last_alert_time >= alert_interval:
                try:
                    tab.refresh()
                    tab.wait(3)
                    qr_code_data = get_login_qrcode(tab, platform)
                    last_alert_time = send_login_card(platform, statu=False, reason="登录已失效",
                                                      screenshot_bytes=qr_code_data)
                except Exception as e:
                    log.error(f"截图失败: {e}")

            elapsed_time = int(current_time - start_wait_time)
            log.info(f"{platform}正在等待扫码，已耗时 {elapsed_time}s...")
            time.sleep(60)

    except Exception as e:
        log.error(f"登录小红书时发生错误: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    browser = Chromium()
    tab = browser.latest_tab
    login_xiaohongshu(tab, alert_interval=300, timeout_limit=1200)