import time
import sentry_sdk
from kuaishou.login_ks import login_kuaishou
from kuaishou.spider_ks import spider_kuaishou
from shipinhao.login_sph import login_shipinhgao
from shipinhao.spider_sph import spider_shipinhao
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
import traceback
from tools.sentry_config import init_sentry

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)
init_sentry()

if getattr(sys, 'frozen', False):  # 如果是打包后的环境
    os.chdir(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable))


def run_douyin_task(browser):
    """执行抖音爬虫任务"""
    try:
        log.info("----------------------开始采集抖音数据----------------------")
        page_douyin = browser.latest_tab
        page_douyin.wait(2)
        login_douyin(page_douyin)
        spider_douyin(page_douyin)
        time.sleep(3)
        log.info("----------------------抖音数据采集完成----------------------")
        return True
    except Exception as e:
        log.error(f"抖音爬虫执行失败: {e}")
        log.error(traceback.format_exc())
        sentry_sdk.capture_exception(e)
        return False


def run_xiaohongshu_task(browser):
    """执行小红书爬虫任务"""
    try:
        log.info("----------------------开始采集小红书数据----------------------")
        page_xiaohongshu = browser.new_tab()
        page_xiaohongshu.wait(2)
        login_xiaohongshu(page_xiaohongshu)
        spider_xiaohongshu(page_xiaohongshu)
        time.sleep(3)
        log.info("----------------------小红书数据采集完成----------------------")
        return True
    except Exception as e:
        log.error(f"小红书爬虫执行失败: {e}")
        log.error(traceback.format_exc())
        sentry_sdk.capture_exception(e)
        return False


def run_kuaishou_task(browser):
    """执行快手爬虫任务"""
    try:
        log.info("----------------------开始采集快手数据----------------------")
        page_kuaishou = browser.new_tab()
        page_kuaishou.wait(2)
        login_kuaishou(page_kuaishou)
        spider_kuaishou(page_kuaishou)
        log.info("----------------------快手数据采集完成----------------------")
        return True
    except Exception as e:
        log.error(f"快手爬虫执行失败: {e}")
        log.error(traceback.format_exc())
        sentry_sdk.capture_exception(e)
        return False


def run_shipinhao_task(browser):
    """执行视频号爬虫任务"""
    try:
        log.info("----------------------开始采集视频号数据----------------------")
        page_shipinhao = browser.new_tab()
        page_shipinhao.wait(2)
        login_shipinhgao(page_shipinhao)
        spider_shipinhao(page_shipinhao)
        time.sleep(3)
        log.info("----------------------视频号数据采集完成----------------------")
        return True
    except Exception as e:
        log.error(f"视频号爬虫执行失败: {e}")
        log.error(traceback.format_exc())
        sentry_sdk.capture_exception(e)
        return False


def main():
    try:
        # 创建浏览器实例
        browser = Chromium()
        browser.wait(2)
        log.info(f"----------------------任务开始执行----------------------")

        # 记录各任务执行结果
        results = {
            "douyin": False,
            "xiaohongshu": False,
            "kuaishou": False,
            "shipinhao": False,
        }

        # 执行抖音任务
        results["douyin"] = run_douyin_task(browser)

        # 执行小红书任务
        results["xiaohongshu"] = run_xiaohongshu_task(browser)

        # 执行快手任务
        results["kuaishou"] = run_kuaishou_task(browser)

        # 执行视频号任务
        results["shipinhao"] = run_shipinhao_task(browser)

        # 统计执行结果
        success_count = sum(results.values())
        total_count = len(results)

        if success_count == total_count:
            log.info(f"----------------------任务全部执行完成----------------------")
        else:
            log.warning(f"----------------------任务执行情况: 成功{success_count}/{total_count}----------------------")
            failed_tasks = [task for task, success in results.items() if not success]
            log.warning(f"----------------------失败的任务: {', '.join(failed_tasks)}----------------------")

        # 完成后关闭浏览器
        browser.quit()

    except Exception as e:
        log.error(f"----------------------主程序发生未预期异常: {e}----------------------")
        log.error(traceback.format_exc())
        sentry_sdk.capture_exception(e)
        bot.send_card_alert(
            title="爬虫",
            task_name="爬虫计划任务运行「异常」时告警-新媒体数据-刘建强",
            run_script_name=f"{__file__}",
            exception_plan="爬虫-新媒体数据-刘建强",
            exception_app="主程序",
            error_message=f"任务失败: {str(e)[:200]}",
            client_ip="10.30.40.150",
            at_all=False,
            at_user_ids=[USER_IDS["刘建强"]]
        )


if __name__ == '__main__':
    hours, minutes, seconds = START_TIME.split(':')
    scheduler = BlockingScheduler()
    scheduler.add_job(func=main, trigger='cron', hour=int(hours), minute=int(minutes), second=int(seconds), timezone='Asia/Shanghai')
    scheduler.start()
