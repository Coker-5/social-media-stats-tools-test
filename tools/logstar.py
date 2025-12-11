# tools/logstar.py
from loguru import logger
from pathlib import Path
import sys

def get_project_root():
    """获取项目根目录（兼容 PyInstaller 打包后）"""
    if getattr(sys, 'frozen', False):
        # 打包后：exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境：本文件所在目录的父级（即项目根目录）
        return Path(__file__).parent.parent

def get_logger():
    """
    统一的日志记录方法，日志文件保存在项目根目录的 logs/ 下
    按日期生成日志文件，每天一个，保留30天并压缩
    """
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # 避免重复添加 handler
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
    )

    # 文件输出
    logger.add(
        str(logs_dir / "app_{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )

    return logger


# 快捷方法
def debug(msg): logger.debug(msg)
def info(msg): logger.info(msg)
def warning(msg): logger.warning(msg)
def error(msg): logger.error(msg)
def critical(msg): logger.critical(msg)