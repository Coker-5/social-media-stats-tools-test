import time
from framework.base_login import BaseLogin, log


class XiaoHongShuLogin(BaseLogin):
    def __init__(self, tab, project_name, config):
        # 【优化1】继承基类，统一初始化逻辑，减少冗余代码
        super().__init__(tab, project_name, config)
        self.platform = "小红书"

    def get_login_qrcode(self):
        """
        获取并处理二维码：处理小红书点击切换、去灰、二值化处理
        """
        self.tab.ele(".css-wemwzq").click()
        self.tab.wait(2)
        self.tab.wait.ele_displayed(".login-box-container", timeout=5)
        login_content = self.tab.ele(".login-box-container")
        qrcode_img = login_content.eles("tag:img")[1]  # 获取第二个img标签

        qrcode_bytes = qrcode_img.src(timeout=5, base64_to_bytes=True)
        return self.process_qrcode_image(qrcode_bytes)


    def check_status(self):
        target_url = "https://creator.xiaohongshu.com/new/home"
        login_container = self.tab.ele(".login-box-container", timeout=2)
        is_home_url = target_url in self.tab.url
        # 没有登录框且处于首页URL则视为登录成功
        return not login_container and is_home_url


    def run_login(self, alert_interval=300, timeout_limit=1200):

        start_time = time.time()
        self.tab.get('https://creator.xiaohongshu.com/new/home')
        self.tab.wait(8)

        if self.check_status():
            log.info(f"{self.platform} 已成功登录")
            return True

        log.warning(f"{self.platform}创作者中心---登录已失效，请重新扫码登录")
        qr_code_data = self.get_login_qrcode()
        last_alert = self.send_login_card(self.platform, False, "登录已失效", qr_code_data)

        while True:
            elapsed_seconds = int(time.time() - start_time)

            if self.check_status():
                log.info(f"{self.platform} 已成功登录")
                self.send_login_card(self.platform, True)
                return True

            if elapsed_seconds > timeout_limit:
                error_msg = f"{self.platform}登录已超时，请联系管理员"
                log.error(f"[{self.project_name}] {error_msg}")
                self.send_login_card(self.platform, False, error_msg)
                return False

            # 每隔一段时间刷新重发
            if time.time() - last_alert > alert_interval:
                self.tab.refresh()
                self.tab.wait(3)
                qr_code_data = self.get_login_qrcode()
                last_alert = self.send_login_card(self.platform, False, "登录已失效", qr_code_data)


            log.info(f"【{self.project_name}】正在等待{self.platform}扫码，已耗时 {elapsed_seconds}s...")
            time.sleep(30)


# 对外暴露统一格式的函数接口
def login_xiaohongshu(tab, project_name, config, alert_interval=480, timeout_limit=7200):
    handler = XiaoHongShuLogin(tab, project_name, config)
    return handler.run_login(alert_interval, timeout_limit)


if __name__ == '__main__':
    from DrissionPage import Chromium
    from tools.config_loader import get_project_config

    tab = Chromium().latest_tab
    p_name = "TEST"
    p_config = get_project_config(p_name)

    login_xiaohongshu(tab, p_name, p_config, alert_interval=60, timeout_limit=240)