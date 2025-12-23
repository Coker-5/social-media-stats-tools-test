# tools/config_loader.py
import json
import sys
from pathlib import Path

def get_project_root():
    """获取项目根目录（兼容打包后）"""
    if getattr(sys, 'frozen', False):
        # 打包后的可执行文件路径
        return Path(sys.executable).parent
    else:
        # 开发环境：config_loader.py 所在目录的父级（即项目根目录）
        return Path(__file__).parent.parent

# 配置文件路径：项目根目录 / config / config.json
_CONFIG_PATH = get_project_root() / "config" / "config.json"

_CONFIG = None

def _load():
    global _CONFIG
    if _CONFIG is None:
        with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
            _CONFIG = json.load(f)
    return _CONFIG

def _get(keys):
    config = _load()
    value = config
    for key in keys:
        value = value[key]
    return value

def _parse_user_ids(user_ids_list):
    """将 [{"用户名": "user_id"}, ...] 格式转换为字典"""
    result = {}
    for item in user_ids_list:
        for name, user_id in item.items():
            result[name] = user_id
    return result



# 导出配置项
# 基础配置
START_TIME = _get(['start_time'])
APP_ID = _get(['feishu_config', 'app_info', 'APP_ID'])
APP_SECRET = _get(['feishu_config', 'app_info', 'APP_SECRET'])
BOT_WEBHOOK = _get(['feishu_config', 'bot_webhook'])

# 表格配置
BASE_TOKEN = _get(['tables', 'base_token'])
TABLE_DY_ACCOUNTS = _get(['tables', 'douyin', 'accounts'])
TABLE_DY_NOTES = _get(['tables', 'douyin', 'notes'])
TABLE_XHS_ACCOUNTS = _get(['tables', 'xiaohongshu', 'accounts'])
TABLE_XHS_NOTES = _get(['tables', 'xiaohongshu', 'notes'])
TABLE_KS_ACCOUNTS = _get(['tables', 'kuaishou', 'accounts'])
TABLE_KS_NOTES = _get(['tables', 'kuaishou', 'notes'])
TABLE_SPH_ACCOUNTS = _get(['tables', 'shipinhao', 'accounts'])
TABLE_SPH_NOTES = _get(['tables', 'shipinhao', 'notes'])

# 用户配置
USER_IDS = _parse_user_ids(_get(['user_ids']))

# sentry配置
SENTRY_DSN = _get(['sentry_dsn'])