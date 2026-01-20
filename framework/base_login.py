import io
import time
from PIL import Image

from tools.config_loader import extract_user_ids
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot

log = get_logger()

class BaseLogin:
    def __init__(self, tab, project_name, config):
        self.tab = tab
        self.project_name = project_name
        feishu_cfg = config.get('feishu_config', {})
        app_info = feishu_cfg.get('app_info', {})
        self.bot = FeishuBot(
            webhook_url=feishu_cfg.get('bot_webhook'),
            app_id=app_info.get('APP_ID'),
            app_secret=app_info.get('APP_SECRET')
        )
        self.config = config
        # 提取当前项目的运营人员
        self.ops_ids = extract_user_ids(config.get('user_ids'), 'operations')

    def process_qrcode_image(self, qrcode_bytes, target_size=(180, 180)):
        """【封装】通用的二维码去灰、二值化处理逻辑"""
        try:
            with Image.open(io.BytesIO(qrcode_bytes)) as img:
                img = img.convert("RGBA")
                # 背景去灰
                canvas = Image.new("RGBA", img.size, (255, 255, 255, 255))
                canvas.paste(img, (0, 0), img)
                # 二值化增强对比度
                gray = canvas.convert("L")
                bw_img = gray.point(lambda x: 0 if x < 200 else 255, '1')
                # 缩放
                final_img = bw_img.convert("RGB").resize(target_size, Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                final_img.save(buf, format='PNG')
                return buf.getvalue()
        except Exception as e:
            log.warning(f"图片处理失败，返回原图: {e}")
            return qrcode_bytes

    def send_login_card(self, platform: str, statu: bool, reason: str = "", screenshot_bytes: bytes = None):
        """ 发送登录通知卡片 """
        if statu:
            self.bot.send_card_success(
                title="登录",
                task_name=f"爬虫-{platform}-新媒体数据采集",
                platform=platform,
                success_message=f"【{platform}】登录成功 "
            )
        else:
            if screenshot_bytes:
                self.bot.send_card_alert(
                    title="登录",
                    title_color="yellow",
                    task_name=f"监控告警-{platform}登录状态",
                    run_script_name=__name__,
                    exception_plan=f"爬虫-{platform}-新媒体数据采集",
                    exception_app=platform,
                    error_message=f"【{platform}】{reason}，请尽快重新扫码登录。",
                    screenshot_bytes=screenshot_bytes,
                    screenshot_text=f"{platform}登录二维码截图：",
                    at_user_ids=self.ops_ids
                )
            else:
                self.bot.send_card_alert(
                    title="登录",
                    title_color="yellow",
                    task_name=f"监控告警-{platform}登录状态",
                    exception_plan=f"爬虫-{platform}-新媒体数据采集",
                    exception_app=platform,
                    error_message=f"【{platform}】{reason}",
                    at_user_ids=self.ops_ids
                )
            log.info(f"发送提醒: {platform} {reason}")

        return time.time()
