from prefect.cache_policies import NO_CACHE
from prefect.client.schemas.schedules import CronSchedule
from kuaishou.login_ks import login_kuaishou
from kuaishou.spider_ks import spider_kuaishou
from shipinhao.login_sph import login_shipinhgao
from shipinhao.spider_sph import spider_shipinhao
from tools.logstar import setup_logger, get_logger
from douyin.login_dy import login_douyin
from douyin.spider_dy import spider_douyin
from tools.send_feishu import FeishuBot
from xiaohongshu.login_xhs import login_xiaohongshu
from xiaohongshu.spider_xhs import spider_xiaohongshu
from DrissionPage import Chromium
from tools.config_loader import (START_TIME, BOT_WEBHOOK, DEVELOPERS_ID_LIST, APP_ID, APP_SECRET)
from tools.sentry_config import init_sentry
from prefect import flow, task

setup_logger()
bot = FeishuBot(BOT_WEBHOOK)
init_sentry()
log = get_logger()


@task(name="抖音", cache_policy=NO_CACHE)
def run_douyin_task(browser):
    """执行抖音爬虫任务"""
    try:
        log.info("----------------------开始采集抖音数据----------------------")
        page = browser.new_tab()
        if login_douyin(page):
            spider_douyin(page)
            log.info("----------------------抖音数据采集完成----------------------")
    except Exception as e:
        log.exception(e)
        raise


@task(name="小红书",  cache_policy=NO_CACHE)
def run_xiaohongshu_task(browser):
    """执行小红书爬虫任务"""
    try:
        log.info("----------------------开始采集小红书数据----------------------")
        page = browser.new_tab()
        if login_xiaohongshu(page):
            spider_xiaohongshu(page)
            log.info("----------------------小红书数据采集完成----------------------")
    except Exception as e:
        log.exception(e)
        raise


@task(name="快手", cache_policy=NO_CACHE)
def run_kuaishou_task(browser):
    """执行快手爬虫任务"""
    try:
        log.info("----------------------开始采集快手数据----------------------")
        page = browser.new_tab()
        if login_kuaishou(page):
            spider_kuaishou(page)
            log.info("----------------------快手数据采集完成----------------------")
    except Exception as e:
        log.exception(e)
        raise


@task(name="视频号", cache_policy=NO_CACHE)
def run_shipinhao_task(browser):
    """执行视频号爬虫任务"""
    try:
        log.info("----------------------开始采集视频号数据----------------------")
        page = browser.new_tab()
        if login_shipinhgao(page):
            spider_shipinhao(page)
            log.info("----------------------视频号数据采集完成----------------------")
    except Exception as e:
        log.exception(e)
        raise


@flow(name="新媒体矩阵爬虫系统", log_prints=True)
def main():
    browser = Chromium()

    try:
        # run_douyin_task(browser)
        # run_xiaohongshu_task(browser)
        run_kuaishou_task(browser)
        run_shipinhao_task(browser)
    finally:
        browser.quit()


if __name__ == '__main__':
    main.serve(
        name="daily-framework-job",
        schedule=CronSchedule(cron="42 11 * * *", timezone="Asia/Shanghai"),
        tags=["media", "drission-page"],
        description="新媒体数据采集系统"
    )
