import sentry_sdk
from prefect import flow, task, get_run_logger, serve
from DrissionPage import Chromium, ChromiumOptions
from prefect.cache_policies import NO_CACHE
from tools.config_loader import get_all_projects, extract_user_ids, get_project_config
from tools.send_feishu import FeishuBot
from tools.router import TASK_ROUTER


@task(name="登录", cache_policy=NO_CACHE)
def login(tab, p_name, p_config, platform_key, route, alert_interval, timeout_limit):
    """
    负责单个平台的登录逻辑
    """
    p_logger = get_run_logger()

    p_logger.info(f"[{p_name}] 执行登录: {platform_key}")

    success = route["login_func"](tab, p_name, p_config, alert_interval, timeout_limit)

    return success


@task(name="采集", cache_policy=NO_CACHE)
def scrape(tab, p_name, p_config, route, actions):
    """
    负责单个平台的采集逻辑
    """
    p_logger = get_run_logger()
    spider_inst = route["spider_class"](tab, p_name, p_config)

    for task_type, is_enabled in actions.items():
        if is_enabled:
            method_name = route["methods"].get(task_type)
            if hasattr(spider_inst, method_name):
                p_logger.info(f"[{p_name}] 运行子任务: {method_name}")
                getattr(spider_inst, method_name)()


@flow(log_prints=True)
def run_single_project_flow(p_name: str):
    """
    接收单个项目名称，读取对应配置并执行
    """
    log = get_run_logger()
    p_config = get_project_config(p_name)

    # --- 项目初始化 (Sentry & Bot) ---
    dsn = p_config.get("sentry_dsn")
    if dsn:
        sentry_sdk.init(dsn=dsn, traces_sample_rate=1.0)

    f_cfg = p_config.get("feishu_config", {})
    bot = FeishuBot(
        webhook_url=f_cfg.get("bot_webhook"),
        app_id=f_cfg.get("app_info", {}).get("APP_ID"),
        app_secret=f_cfg.get("app_info", {}).get("APP_SECRET")
    )

    log.info(f"🚀 启动项目 Flow: {p_name}")

    co = ChromiumOptions()
    if p_config.get("browser_id"):
        co.set_user_data_path(f"./browser_data/{p_config.get('browser_id')}")

    browser = Chromium(co)

    try:
        tasks = p_config.get("tasks", {})
        for platform_key, actions in tasks.items():
            route = TASK_ROUTER.get(platform_key)
            if not route or not any(actions.values()):
                continue

            target_tab = browser.new_tab()
            # 执行登录逻辑
            login_ok = login(target_tab, p_name, p_config, platform_key, route, alert_interval=60, timeout_limit=150)

            if login_ok:
                scrape(target_tab, p_name, p_config, route, actions)


    except Exception as e:
        log.error(f"项目 {p_name} 发生异常: {e}")
        sentry_sdk.capture_exception(e)
        dev_ids = extract_user_ids(p_config.get("user_ids"), 'developers')
        bot.send_card_alert(
            title="爬虫",
            task_name="爬虫计划任务运行「异常」时告警-新媒体数据-刘建强",
            run_script_name=f"{__file__}",
            exception_plan="爬虫-新媒体数据-刘建强",
            exception_app="主程序",
            error_message=f"任务失败: {str(e)[:200]}",
            client_ip="10.30.40.150",
            at_all=False,
            at_user_ids=dev_ids
        )
    finally:
        browser.quit()


def run():
    # 1. 获取所有启用的项目
    all_projects = get_all_projects()
    deployments = []

    # 2. 遍历配置，动态生成部署对象
    for p_name, p_config in all_projects.items():

        start_time_str = p_config.get("start_time")
        h, m, _ = start_time_str.split(':')
        cron_expr = f"{int(m)} {int(h)} * * *"

        # 将 Flow 转换为 Deployment 对象
        p_dep = run_single_project_flow.to_deployment(
            name=f"dep-{p_name}",
            parameters={"p_name": p_name},
            cron=cron_expr,
            description=f"项目 {p_name} 的采集任务，每日 {start_time_str} 启动"
        )
        deployments.append(p_dep)
        print(f"✅ 已加载项目模块 [{p_name}] -> 计划时间: {start_time_str} (Cron: {cron_expr})")

    # 3. 启动 Prefect 调度服务
    print(f"📢 Prefect Serve 启动中，正在监听 {len(deployments)} 个项目的定时任务...")

    # serve 是阻塞运行的，它会维持心跳并根据 Cron 触发 flow
    serve(*deployments)


if __name__ == '__main__':
    run()