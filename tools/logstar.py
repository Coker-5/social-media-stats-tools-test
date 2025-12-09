from loguru import logger
from pathlib import Path


def get_logger(file_path):
    """
    统一的日志记录方法，自动识别调用文件并单独保存日志，日志级别 (debug, info, warning, error, critical)
    """
    file_name = Path(file_path).stem

    # 配置日志文件，使用 {file} 代替 {name}
    logger.add(
        f"logs/{file_name}.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {file}:{line} | {message}",
        rotation="10 MB",
        retention="30 days"
    )

    return logger


# 快捷方法保持不变
def debug(msg): logger.debug(msg)


def info(msg): logger.info(msg)


def error(msg): logger.error(msg)