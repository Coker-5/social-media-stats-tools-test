# sentry_config.py
import sentry_sdk
from tools.config_loader import SENTRY_DSN



def init_sentry():
    """初始化Sentry配置"""

    # 从环境变量读取DSN
    dsn = SENTRY_DSN
    if not dsn:
        return


    sentry_sdk.init(
        dsn=dsn,
        send_default_pii=True,
        traces_sample_rate=1.0,
        # 忽略特定异常
        ignore_errors=[
            "KeyboardInterrupt",  # Ctrl+C
        ]
    )
