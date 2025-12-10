from loguru import logger
from pathlib import Path
import sys


def get_logger():
    """
    统一的日志记录方法，日志文件统一保存在项目根目录的logs文件夹下
    按日期生成日志文件，每天一个文件
    """
    # 获取项目根目录路径
    current_dir = Path(__file__).parent
    project_root = current_dir.parent  # 项目根目录

    # 构建logs目录路径
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)  # 确保logs目录存在

    # 删除所有已添加的处理器（避免重复添加）
    logger.remove()

    # 配置控制台输出
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
    )

    # 配置文件输出 - 按日期轮转
    logger.add(
        str(logs_dir / "app_{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="00:00",  # 每天0点创建新文件
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        encoding="utf-8"
    )

    return logger




# 快捷方法
def debug(msg): logger.debug(msg)


def info(msg): logger.info(msg)


def warning(msg): logger.warning(msg)


def error(msg): logger.error(msg)


def critical(msg): logger.critical(msg)