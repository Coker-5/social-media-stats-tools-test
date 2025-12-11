import time
from tools.logstar import get_logger
from douyin.login_dy import login_douyin
from douyin.spider_dy import spider_douyin
from xiaohongshu.login_xhs import login_xiaohongshu
from xiaohongshu.spider_xhs import spider_xiaohongshu
from apscheduler.schedulers.blocking import BlockingScheduler
from DrissionPage import Chromium
from tools.config_loader import (START_TIME)
import os
import sys

log = get_logger()

if getattr(sys, 'frozen', False):  # 如果是打包后的环境
    os.chdir(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable))


def main():
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



if __name__ == '__main__':
    hours, minutes, seconds = START_TIME.split(':')
    scheduler = BlockingScheduler()
    scheduler.add_job(func=main, trigger='cron', hour=int(hours), minute=int(minutes), second=int(seconds), timezone='Asia/Shanghai')
    scheduler.start()
