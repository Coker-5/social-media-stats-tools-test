import io
import time
from DrissionPage import Chromium
from PIL import Image

from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.config_loader import (BOT_WEBHOOK, OPERATIONS_ID_LIST, APP_ID, APP_SECRET)

log = get_logger()
# 初始化bot，传入APP_ID和APP_SECRET以支持二维码图片上传
bot = FeishuBot(BOT_WEBHOOK, APP_ID, APP_SECRET)


def get_login_qrcode(tab, platform, target_size=(180, 180)):
    """
    获取并处理抖音登录二维码：强制黑白化、去灰、二值化处理
    """
    try:
        # 等待抖音登录组件加载
        tab.wait.ele_displayed('#douyin_login_comp_scan_code', timeout=5)
        login_content = tab.ele("#douyin_login_comp_scan_code")
        qrcode_img = login_content.ele("tag:img")

        if qrcode_img:
            qrcode_bytes = qrcode_img.src(timeout=5, base64_to_bytes=True)
            if not qrcode_bytes: return None

            try:
                with Image.open(io.BytesIO(qrcode_bytes)) as img:
                    # 第一步：转为 RGBA 确保能处理透明度
                    img = img.convert("RGBA")

                    # 第二步：背景去灰处理（白色底）
                    canvas = Image.new("RGBA", img.size, (255, 255, 255, 255))
                    canvas.paste(img, (0, 0), img)

                    # 第三步：转为灰度图并进行“二值化”处理，增强对比度
                    gray = canvas.convert("L")
                    bw_img = gray.point(lambda x: 0 if x < 200 else 255, '1')

                    # 第四步：转回 RGB 并调整尺寸
                    final_img = bw_img.convert("RGB")
                    final_img = final_img.resize(target_size, Image.Resampling.LANCZOS)

                    # 转化为字节流用于发送
                    buf = io.BytesIO()
                    final_img.save(buf, format='PNG')
                    return buf.getvalue()

            except Exception as e:
                log.warning(f"图片像素处理失败: {e}")
                return qrcode_bytes
    except Exception as e:
        log.error(f"获取二维码失败: {e}")
        return None


def is_douyin_login(page_douyin):
    """
    检查抖音是否已登录
    """
    target_url = "https://creator.douyin.com/creator-micro/home"
    try:
        # 检查是否还有登录容器
        login_container = page_douyin.ele(".flat_container-FFKCgg", timeout=2)
        # 检查当前URL是否为创作者首页
        is_home_url = target_url in page_douyin.url

        if not login_container and is_home_url:
            return True
        else:
            return False
    except Exception as e:
        log.warning(f"检查抖音登录状态时发生错误: {e}")
        return False


def send_login_card(platform: str, statu: bool, reason: str = "", screenshot_bytes: bytes = None):
    """
    发送登录通知卡片（参考视频号标准）
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


def login_douyin(page_douyin, alert_interval=300, timeout_limit=1200):
    """
    登录抖音创作者中心
    :param page_douyin: 浏览器标签页对象
    :param alert_interval: 告警频率间隔（秒），默认5分钟
    :param timeout_limit: 最大等待扫码时间（秒），默认20分钟
    """
    try:
        tab = page_douyin
        platform = "抖音"

        tab.get('https://creator.douyin.com/')
        tab.wait(8)

        start_wait_time = time.time()
        last_alert_time = 0

        # 1. 检查初始登录状态
        if is_douyin_login(tab):
            log.info(f"{platform}创作者中心---已成功登录")
            return True
        else:
            log.warning(f"{platform}创作者中心---登录已失效，请重新扫码登录")
            # 获取二维码并发送初始告警
            qr_code_data = get_login_qrcode(tab, platform)
            last_alert_time = send_login_card(platform, statu=False, reason="登录已失效",
                                              screenshot_bytes=qr_code_data)

        # 2. 等待登录循环
        while True:
            current_time = time.time()

            # 检查是否扫码成功
            if is_douyin_login(tab):
                log.info(f"{platform}创作者中心---已成功登录")
                send_login_card(platform=platform, statu=True)
                return True

            # 检查是否超时
            if current_time - start_wait_time > timeout_limit:
                error_msg = f"{platform}登录已超时，请联系管理员"
                log.error(error_msg)
                send_login_card(platform, statu=False, reason=error_msg)
                return False

            # 定时刷新二维码并发送提醒（防止码过期）
            if current_time - last_alert_time >= alert_interval:
                try:
                    tab.refresh()
                    tab.wait(3)
                    qr_code_data = get_login_qrcode(tab, platform)
                    last_alert_time = send_login_card(platform, statu=False, reason="登录已失效",
                                                      screenshot_bytes=qr_code_data)
                except Exception as e:
                    log.error(f"截图失败: {e}")

            # 日志轮询进度
            elapsed_time = int(current_time - start_wait_time)
            log.info(f"{platform}正在等待扫码，已耗时 {elapsed_time}s...")
            time.sleep(60)

    except Exception as e:
        log.error(f"登录抖音时发生错误: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    # 初始化浏览器
    browser = Chromium()
    tab = browser.latest_tab
    # 执行登录流程
    login_douyin(tab, alert_interval=200, timeout_limit=1200)