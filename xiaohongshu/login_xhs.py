import time
from DrissionPage import Chromium
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot

log = get_logger(__file__)
tab = Chromium()
bot = FeishuBot("https://open.feishu.cn/open-apis/bot/v2/hook/a0f02537-1227-4e6b-a501-f7816723ee42")

def login_xiaohongshu():
    global tab
    tab=tab.new_tab('https://creator.xiaohongshu.com/new/home')
    tab.wait(2)

    login_btn = tab.ele(".login-box-container",timeout=2)
    if login_btn:
        log.warning("小红书创作者中心---登录已失效，请重新扫码登录")
        bot.send_text(text="【 小红书创作者中心 】登录已失效，请重新扫码登录",at_all=True)
        while True:
            log.info("登录状态检查中...")
            login_btn = tab.ele(".login-box-container")
            if not login_btn and tab.url == "https://creator.xiaohongshu.com/new/home":
                break
            bot.send_text(text="【 小红书创作者中心 】登录已失效，请重新扫码登录", at_all=True)
            time.sleep(20)
    log.info("小红书创作者中心---已成功登录")



if __name__ == '__main__':
    login_xiaohongshu()