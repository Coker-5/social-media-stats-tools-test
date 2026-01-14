# tools/logstar.py
from pathlib import Path
import sys
from loguru import logger
import logging


# 创建自定义Handler将loguru日志转发到logging
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # 获取对应的loguru日志级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 找到调用者
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def get_project_root():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def setup_logger():
    """
    初始化日志配置：此函数在 main 入口调用一次即可
    """
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # 1. 清除 loguru 默认的控制台 Handler
    logger.remove()

    # 2. 配置控制台输出
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
    )

    # 3. 配置定期滚动的日志文件
    logger.add(
        str(logs_dir / "app_{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="00:00",
        retention="30 days",
        encoding="utf-8",
        enqueue=True
    )

    # 4. 将标准logging模块的日志转发到loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # # 5. 禁用某些过于冗长的日志
    # for _log in ["urllib3", "selenium", "DrissionPage", "prefect"]:
    #     logging.getLogger(_log).setLevel(logging.WARNING)

    return logger


class LogProxy:
    """
    日志代理类
    """

    def __getattr__(self, name):
        return getattr(logger, name)

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        pass


# 预实例化一个代理对象
_proxy_log = LogProxy()


def get_logger():
    return _proxy_log


# 兼容直接从模块导入 log 的写法
log = _proxy_log