import io
import time
from DrissionPage import Chromium
from PIL import Image

from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.config_loader import (BOT_WEBHOOK, OPERATIONS_ID_LIST, APP_ID, APP_SECRET)

log = get_logger()
# 初始化bot，传入APP_ID和APP_SECRET以支持图片上传展示
bot = FeishuBot(BOT_WEBHOOK, APP_ID, APP_SECRET)


def get_login_qrcode(tab, platform, target_size=(180, 180)):
    """
    获取并处理快手二维码：处理切换、强制黑白化、去灰
    """
    try:
        tab.get("https://passport.kuaishou.com/pc/account/login/?sid=kuaishou.web.cp.api&callback=https://cp.kuaishou.com/rest/infra/sts?followUrl=https%3A%2F%2Fcp.kuaishou.com%2Fprofile&setRootDomain=true")
        tab.wait(3)
        # 快手登录框有时默认是验证码，尝试切换到扫码登录
        if tab.ele("text:扫码登录", timeout=3):
            tab.ele("text:扫码登录").click()
            tab.wait(1)

        # 定位二维码图片
        tab.wait.ele_displayed("@alt=qrcode", timeout=5)
        qrcode_img = tab.ele("@alt=qrcode")

        if qrcode_img:
            qrcode_bytes = qrcode_img.src(timeout=5, base64_to_bytes=True)
            if not qrcode_bytes: return None

            try:
                with Image.open(io.BytesIO(qrcode_bytes)) as img:
                    # 1. 处理透明度
                    img = img.convert("RGBA")

                    # 2. 填充白底去掉灰色背景
                    canvas = Image.new("RGBA", img.size, (255, 255, 255, 255))
                    canvas.paste(img, (0, 0), img)

                    # 3. 灰度化与二值化（增强对比度）
                    gray = canvas.convert("L")
                    bw_img = gray.point(lambda x: 0 if x < 200 else 255, '1')

                    # 4. 调整尺寸并转换格式
                    final_img = bw_img.convert("RGB")
                    final_img = final_img.resize(target_size, Image.Resampling.LANCZOS)

                    buf = io.BytesIO()
                    final_img.save(buf, format='PNG')
                    return buf.getvalue()

            except Exception as e:
                log.warning(f"图片像素处理失败: {e}")
                return qrcode_bytes
    except Exception as e:
        log.error(f"获取二维码失败: {e}")
        return None


def is_kuaishou_login(page_kuaishou):
    """
    检查快手是否已登录
    """
    try:
        # 检查是否存在登录按钮或登录容器
        login_btn = page_kuaishou.ele(".login", timeout=2)

        # 检查URL是否停留在登录页
        url_contains_login = "login" in page_kuaishou.url

        # 如果没有登录按钮且URL不是登录页，则认为已登录
        if not login_btn and not url_contains_login:
            return True
        else:
            return False

    except Exception as e:
        # 兜底逻辑：如果URL中没有login，通常表示已经跳转进后台
        if "login" not in page_kuaishou.url:
            return True
        log.warning(f"检查快手登录状态时发生错误: {e}")
        return False


def send_login_card(platform: str, statu: bool, reason: str = "", screenshot_bytes: bytes = None):
    """
    发送登录通知卡片
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
                screenshot_text=f"{platform}最新扫码二维码：",
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


def login_kuaishou(page_kuaishou, alert_interval=300, timeout_limit=1200):
    """
    登录快手创作者中心
    :param page_kuaishou: 浏览器标签页对象
    :param alert_interval: 告警频率间隔（秒），默认5分钟
    :param timeout_limit: 最大等待扫码时间（秒），默认20分钟
    """
    try:
        tab = page_kuaishou
        platform = "快手"

        tab.get('https://cp.kuaishou.com/profile')
        tab.wait(3)

        start_wait_time = time.time()
        last_alert_time = 0

        # 1. 检查初始状态
        if is_kuaishou_login(tab):
            log.info(f"{platform}创作者中心---已成功登录")
            return True
        else:
            log.warning(f"{platform}创作者中心---登录已失效，请重新扫码登录")
            qr_code_data = get_login_qrcode(tab, platform)
            last_alert_time = send_login_card(platform, statu=False, reason="登录已失效",
                                              screenshot_bytes=qr_code_data)

        # 2. 等待扫码循环
        while True:
            current_time = time.time()

            # 扫码成功判定
            if is_kuaishou_login(tab):
                log.info(f"{platform}创作者中心---已成功登录")
                send_login_card(platform=platform, statu=True)
                return True

            # 超时判定
            if current_time - start_wait_time > timeout_limit:
                error_msg = f"{platform}登录已超时，请联系管理员"
                log.error(error_msg)
                send_login_card(platform, statu=False, reason=error_msg)
                return False

            # 定时刷新二维码并重新提醒
            if current_time - last_alert_time >= alert_interval:
                try:
                    qr_code_data = get_login_qrcode(tab, platform)
                    last_alert_time = send_login_card(platform, statu=False, reason="登录已失效",
                                                      screenshot_bytes=qr_code_data)
                except Exception as e:
                    log.error(f"截图失败: {e}")

            # 打印轮询日志
            elapsed_time = int(current_time - start_wait_time)
            log.info(f"{platform}正在等待扫码，已耗时 {elapsed_time}s...")
            time.sleep(60)

    except Exception as e:
        log.error(f"登录快手时发生错误: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    # 示例运行逻辑
    browser = Chromium()
    tab = browser.latest_tab
    login_kuaishou(tab, alert_interval=60, timeout_limit=1200)