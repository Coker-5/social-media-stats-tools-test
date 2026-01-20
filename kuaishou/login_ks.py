import time
from framework.base_login import BaseLogin, log


class KuaishouLogin(BaseLogin):
    def __init__(self, tab, project_name, config):
        # 【优化1】调用基类初始化，统一管理 project_name 和 config
        super().__init__(tab, project_name, config)
        self.platform = "快手"

    def get_login_qrcode(self):
        """
        获取并处理快手二维码：处理切换、强制黑白化、去灰
        """
        self.tab.get(
            "https://passport.kuaishou.com/pc/account/login/?sid=kuaishou.web.cp.api&callback=https://cp.kuaishou.com/rest/infra/sts?followUrl=https%3A%2F%2Fcp.kuaishou.com%2Fprofile&setRootDomain=true")
        self.tab.wait(3)

        if self.tab.ele("text:扫码登录", timeout=3):
            self.tab.ele("text:扫码登录").click()
            self.tab.wait(1)

        self.tab.wait.ele_displayed("@alt=qrcode", timeout=5)
        qrcode_img = self.tab.ele("@alt=qrcode")
        qrcode_bytes = qrcode_img.src(timeout=5, base64_to_bytes=True)
        return self.process_qrcode_image(qrcode_bytes)


    def check_status(self):

        login_btn = self.tab.ele(".login", timeout=2)
        url_contains_login = "login" in self.tab.url

        if not login_btn and not url_contains_login:
            return True
        else:
            return False


    def run_login(self, alert_interval=300, timeout_limit=1200):

        start_time = time.time()
        self.tab.get('https://cp.kuaishou.com/profile')
        self.tab.wait(8)

        if self.check_status():
            log.info(f"{self.platform} 已成功登录")
            return True

        # 1. 第一次获取并发送
        log.warning(f"{self.platform}创作者中心---登录已失效，请重新扫码登录")
        qr_code_data = self.get_login_qrcode()
        last_alert = self.send_login_card(self.platform, False, "登录已失效", qr_code_data)

        # 2. 循环等待
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

            # 每隔一段时间刷新重发
            if time.time() - last_alert > alert_interval:
                qr_code_data = self.get_login_qrcode()
                last_alert = self.send_login_card(self.platform, False, "登录已失效", qr_code_data)

            log.info(f"【{self.project_name}】正在等待扫码，已耗时 {elapsed_seconds}s...")
            time.sleep(30)


def login_kuaishou(tab, project_name, config, alert_interval=480, timeout_limit=7200):
    handler = KuaishouLogin(tab, project_name, config)
    return handler.run_login(alert_interval, timeout_limit)


if __name__ == '__main__':
    from DrissionPage import Chromium
    from tools.config_loader import get_project_config

    tab = Chromium().latest_tab
    p_name = "TEST"
    p_config = get_project_config(p_name)

    login_kuaishou(tab, p_name, p_config, alert_interval=60, timeout_limit=240)