import time
from framework.base_login import BaseLogin, log

class ShipinhgaoLogin(BaseLogin):
    def __init__(self, tab, project_name, config):
        # 继承基类，统一初始化项目名称、配置和平台名
        super().__init__(tab, project_name, config)
        self.platform = "视频号"

    def get_login_qrcode(self):
        """
        获取并处理二维码：强制黑白化、去灰、保存本地
        """
        # 视频号特有逻辑：需要处理 iframe 穿透
        self.tab.wait.ele_displayed(".login-content", timeout=5)
        login_content = self.tab.ele(".login-content")
        iframe = login_content.get_frame(1)
        qrcode_img = iframe.ele("tag:img")
        qrcode_bytes = qrcode_img.src(timeout=5, base64_to_bytes=True)
        return self.process_qrcode_image(qrcode_bytes)



    def check_status(self):
        """
        检查视频号是否已登录：通过元素和URL双重判定
        """
        # 检查登录组件是否存在
        login_btn = self.tab.ele(".login-content", timeout=2)
        # 检查URL是否包含登录页面标识
        is_login_page = "login" in self.tab.url.lower()

        # 如果没有登录组件且不在登录页面，则表示已登录
        return not login_btn and not is_login_page

    def run_login(self, alert_interval=300, timeout_limit=1200):
        """
        执行登录循环：包含初始检查、二维码发送、超时判定及定时刷新
        """
        start_time = time.time()
        self.tab.get('https://channels.weixin.qq.com/platform')
        self.tab.wait(8)

        if self.check_status():
            log.info(f"{self.platform} 已成功登录")
            return True

        # 1. 第一次获取并发送二维码
        log.warning(f"{self.platform}创作者中心---登录已失效，请重新扫码登录")
        qr_code_data = self.get_login_qrcode()
        last_alert = self.send_login_card(self.platform, False, "登录已失效", qr_code_data)

        # 2. 循环等待扫码
        while True:
            elapsed_seconds = int(time.time() - start_time)

            if self.check_status():
                log.info(f"{self.platform} 已成功登录")
                self.send_login_card(self.platform, True)
                return True

            if elapsed_seconds > timeout_limit:
                error_msg = f"登录已超时，请联系管理员"
                log.error(f"[{self.project_name}] {error_msg}")
                self.send_login_card(self.platform, False, error_msg)
                return False

            # 每隔一段时间刷新重发，防止二维码过期
            if time.time() - last_alert > alert_interval:
                self.tab.refresh()
                self.tab.wait(3)
                qr_code_data = self.get_login_qrcode()
                last_alert = self.send_login_card(self.platform, False, "登录已失效", qr_code_data)


            log.info(f"【{self.project_name}】正在等待{self.platform}扫码，已耗时 {elapsed_seconds}s...")
            time.sleep(30)


# 给外部调用的统一接口函数
def login_shipinhao(tab, project_name, config, alert_interval=300, timeout_limit=1200):
    handler = ShipinhgaoLogin(tab, project_name, config)
    return handler.run_login(alert_interval, timeout_limit)


if __name__ == '__main__':
    from DrissionPage import Chromium
    from tools.config_loader import get_project_config

    tab = Chromium().latest_tab
    p_name = "TEST"
    p_config = get_project_config(p_name)

    login_shipinhao(tab, p_name, p_config, alert_interval=60, timeout_limit=200)