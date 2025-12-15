import time
from tools.logstar import get_logger
from douyin.login_dy import login_douyin
from douyin.spider_dy import spider_douyin
from tools.send_feishu import FeishuBot
from xiaohongshu.login_xhs import login_xiaohongshu
from xiaohongshu.spider_xhs import spider_xiaohongshu
from apscheduler.schedulers.blocking import BlockingScheduler
from DrissionPage import Chromium
from tools.config_loader import (START_TIME, BOT_WEBHOOK, USER_IDS)
import os
import sys

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)

if getattr(sys, 'frozen', False):  # 如果是打包后的环境
    os.chdir(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable))


def main():
    try:
        # 创建浏览器实例
        browser = Chromium()
        page_douyin = browser.latest_tab
        browser.wait(2)
        log.info(f"----------------------任务开始执行----------------------")

        log.info("----------------------开始采集抖音数据----------------------")
        login_douyin(page_douyin)
        spider_douyin(page_douyin)

        time.sleep(3)

        log.info("----------------------开始采集小红书数据----------------------")
        page_xiaohongshu = browser.new_tab()
        page_xiaohongshu.wait(2)
        login_xiaohongshu(page_xiaohongshu)
        spider_xiaohongshu(page_xiaohongshu)

        # 完成后关闭浏览器
        browser.quit()
        log.info(f"----------------------任务执行完成----------------------")
    except Exception as e:
        log.error(e)
        bot.send_card_alert(
            title="爬虫",
            task_name="爬虫计划任务运行「异常」时告警-新媒体数据-刘建强",
            run_script_name=f"{__file__}",
            exception_plan="爬虫-新媒体数据-刘建强",
            exception_app="主程序",
            error_message=f"任务失败，{e}",
            client_ip="10.30.40.150",
            at_all=False,
            at_user_ids=[USER_IDS["刘建强"]]
        )



if __name__ == '__main__':
    hours, minutes, seconds = START_TIME.split(':')
    scheduler = BlockingScheduler()
    scheduler.add_job(func=main, trigger='cron', hour=int(hours), minute=int(minutes), second=int(seconds), timezone='Asia/Shanghai')
    scheduler.start()
