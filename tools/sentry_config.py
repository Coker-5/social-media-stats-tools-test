import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from tools.config_loader import SENTRY_DSN

def init_sentry():
    """初始化Sentry配置"""
    dsn = SENTRY_DSN
    if not dsn:
        return

    # 配置日志集成
    sentry_logging = LoggingIntegration(
        level=logging.INFO,        # 将 INFO 及以上的日志作为面包屑 (Breadcrumbs)
        event_level=logging.ERROR  # 将 ERROR 及以上的日志直接发送为 Sentry 事件，并尝试带上堆栈
    )

    sentry_sdk.init(
        dsn=dsn,
        send_default_pii=True,
        include_local_variables=True, # 必须确保此项打开，用于捕捉变量
        integrations=[sentry_logging],
        traces_sample_rate=1.0,
        ignore_errors=["KeyboardInterrupt"]
    )