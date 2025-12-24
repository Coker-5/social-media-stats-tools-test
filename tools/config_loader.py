import json
import sys
from pathlib import Path

def get_project_root():
    """获取项目根目录（兼容打包后）"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent

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


def _extract_ids_from_groups(user_config):
    """
    遍历 user_ids 下的所有组（operations, developers 等），
    提取所有的 user_id 并返回一个去重后的列表。
    """
    all_ids = []
    for group_name in user_config:
        group_list = user_config[group_name]
        for item in group_list:
            all_ids.extend(item.values())
    return list(set(all_ids))

# --- 导出配置项 ---

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

# --- 用户配置修改部分 ---

_user_ids_raw = _get(['user_ids'])

# 所有人
USER_ID_LIST = _extract_ids_from_groups(_user_ids_raw)

# 导出运营人员 ID
OPERATIONS_ID_LIST = [list(d.values())[0] for d in _user_ids_raw['operations']]

# 导出开发人员 ID
DEVELOPERS_ID_LIST = [list(d.values())[0] for d in _user_ids_raw['developers']]


# sentry配置
SENTRY_DSN = _get(['sentry_dsn'])