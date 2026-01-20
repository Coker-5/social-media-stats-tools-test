from framework.base_login import BaseLogin, log
import time


class DouyinLogin(BaseLogin):
    def __init__(self, tab, project_name, config):
        super().__init__(tab, project_name, config)
        self.platform = "抖音"

    def get_login_qrcode(self):
        self.tab.wait.ele_displayed('#douyin_login_comp_scan_code', timeout=5)
        login_content = self.tab.ele("#douyin_login_comp_scan_code")
        qrcode_img = login_content.ele("tag:img")

        qrcode_bytes = qrcode_img.src(timeout=5, base64_to_bytes=True)
        return self.process_qrcode_image(qrcode_bytes)


    def check_status(self):
        target_url = "https://creator.douyin.com/creator-micro/home"
        # 检查是否还有登录容器
        login_container = self.tab.ele(".flat_container-FFKCgg", timeout=2)
        # 检查当前URL是否为创作者首页
        is_home_url = target_url in self.tab.url

        if not login_container and is_home_url:
            return True
        else:
            return False


    def run_login(self, alert_interval=480, timeout_limit=7200):

        start_time = time.time()

        self.tab.get('https://creator.douyin.com/')
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
                self.tab.refresh()
                self.tab.wait(3)
                qr_code_data = self.get_login_qrcode()
                last_alert = self.send_login_card(self.platform, False, "登录已失效", qr_code_data)

            log.info(f"【{self.project_name}】正在等待扫码，已耗时 {elapsed_seconds}s...")
            time.sleep(30)


# 给外部调用的接口
def login_douyin(tab, project_name, config, alert_interval=480, timeout_limit=7200):
    handler = DouyinLogin(tab, project_name, config)
    return handler.run_login(alert_interval, timeout_limit)


if __name__ == '__main__':
    from DrissionPage import Chromium
    from tools.config_loader import get_project_config

    tab = Chromium().latest_tab

    p_name = "TEST"
    p_config = get_project_config(p_name)

    login_douyin(tab=tab, project_name=p_name, config=p_config, alert_interval=60, timeout_limit=130)
