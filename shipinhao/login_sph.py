import time
from DrissionPage import Chromium
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.config_loader import (BOT_WEBHOOK, OPERATIONS_ID_LIST, APP_ID, APP_SECRET)
from PIL import Image
import io

log = get_logger()
# 修改bot初始化，传入APP_ID和APP_SECRET以支持图片上传
bot = FeishuBot(BOT_WEBHOOK, APP_ID, APP_SECRET)


def get_login_qrcode(tab, platform, target_size=(180, 180)):
    """
    获取并处理二维码：强制黑白化、去灰、保存本地
    """
    try:
        tab.wait.ele_displayed(".login-content", timeout=5)
        login_content = tab.ele(".login-content")
        iframe = login_content.get_frame(1)
        qrcode_img = iframe.ele("tag:img")

        if qrcode_img:
            qrcode_bytes = qrcode_img.src(timeout=5, base64_to_bytes=True)
            if not qrcode_bytes: return None

            try:
                with Image.open(io.BytesIO(qrcode_bytes)) as img:
                    # 第一步：转为 RGBA 确保能处理透明度
                    img = img.convert("RGBA")

                    # 第二步：处理“灰色”问题。创建一个白底，将原图贴上去
                    canvas = Image.new("RGBA", img.size, (255, 255, 255, 255))
                    canvas.paste(img, (0, 0), img)

                    # 第三步：转为灰度图并进行“二值化”处理
                    # 只要像素亮度低于200（偏黑/偏灰），强转为0（纯黑）；否则转为255（纯白）
                    gray = canvas.convert("L")
                    bw_img = gray.point(lambda x: 0 if x < 200 else 255, '1')

                    # 转回 RGB 模式
                    final_img = bw_img.convert("RGB")

                    # 第四步：调整尺寸
                    final_img = final_img.resize(target_size, Image.Resampling.LANCZOS)

                    # 返回给飞书发送
                    buf = io.BytesIO()
                    final_img.save(buf, format='PNG')
                    return buf.getvalue()

            except Exception as e:
                log.warning(f"图片像素处理失败: {e}")
                return qrcode_bytes
    except Exception as e:
        log.error(f"获取二维码失败: {e}")
        return None


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


def send_login_card(platform: str, statu: bool, reason: str = "", screenshot_bytes: bytes = None):
    """发送登录通知"""

    if statu:
        bot.send_card_success(
            title="登录",
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
                screenshot_text=f"{platform}登录二维码截图：",
                at_user_ids=OPERATIONS_ID_LIST
            )
        else:
            bot.send_card_alert(
                title="登录",
                title_color="yellow",
                task_name=f"监控告警-{platform}登录状态",
                exception_plan=f"爬虫-{platform}-新媒体数据采集",
                exception_app=platform,
                error_message=f"【{platform}】{reason}",
                at_user_ids=OPERATIONS_ID_LIST
            )


        log.info(f"发送提醒: {platform} {reason}")

    return time.time()


def login_shipinhgao(page_shipinhgao, alert_interval=300, timeout_limit=1200):
    """
    登录视频号创作者中心
    :param page_shipinhgao: 浏览器标签页对象
    :param alert_interval: 告警频率间隔（秒），默认5分钟
    :param timeout_limit: 最大等待扫码时间（秒），默认20分钟
    """
    try:
        tab = page_shipinhgao
        platform = "视频号"

        tab.get('https://channels.weixin.qq.com/platform')
        tab.wait(8)

        start_wait_time = time.time()
        last_alert_time = 0


        # 检查初始登录状态
        if is_shipinhgao_login(tab):
            log.info(f"{platform}创作者中心---已成功登录")
            return True
        else:
            log.warning(f"{platform}创作者中心---登录已失效，请重新扫码登录")
            # 截取并发送截图
            qr_code_data = get_login_qrcode(tab, platform)

            last_alert_time = send_login_card(platform, statu=False, reason="登录已失效",
                                              screenshot_bytes=qr_code_data)

        # 等待登录循环
        while True:
            current_time = time.time()

            if is_shipinhgao_login(tab):
                log.info(f"{platform}创作者中心---已成功登录")
                send_login_card(platform=platform, statu=True)
                return True

            if current_time - start_wait_time > timeout_limit:
                error_msg = f"{platform}登录已超时，请联系管理员"
                log.error(error_msg)
                send_login_card(platform, statu=False, reason=f"登录已超时，请联系管理员")
                return False

            if current_time - last_alert_time >= alert_interval:
                try:
                    tab.refresh()
                    tab.wait(2)
                    qr_code_data = get_login_qrcode(tab, platform)
                    last_alert_time = send_login_card(platform, statu=False, reason="登录已失效",
                                                      screenshot_bytes=qr_code_data)
                except Exception as e:
                    log.error(f"截图失败: {e}")


            # 轮询间隔
            elapsed_time = int(current_time - start_wait_time)
            log.info(f"{platform}正在等待扫码，已耗时 {elapsed_time}s...")
            time.sleep(60)

    except Exception as e:
        log.error(f"登录视频号时发生错误: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    browser = Chromium()
    tab = browser.latest_tab
    login_shipinhgao(tab, alert_interval=60, timeout_limit=1200)