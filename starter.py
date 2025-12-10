import time
from tools.logstar import get_logger
from douyin.login_dy import login_douyin
from douyin.spider_dy import spider_douyin
from xiaohongshu.login_xhs import login_xiaohongshu
from xiaohongshu.spider_xhs import spider_xiaohongshu

log = get_logger()

if __name__ == '__main__':

    log.info("----------------------开始采集抖音数据----------------------")
    login_douyin()
    spider_douyin()

    time.sleep(3)

    log.info("----------------------开始采集小红书数据----------------------")
    login_xiaohongshu()
    spider_xiaohongshu()