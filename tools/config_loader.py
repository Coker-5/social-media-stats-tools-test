import json

# 加载配置
_CONFIG = None

def _load():
    """加载配置"""
    global _CONFIG
    if _CONFIG is None:
        with open('config.json', 'r', encoding='utf-8') as f:
            _CONFIG = json.load(f)
    return _CONFIG

# 导出配置变量
def _get(keys):
    """获取嵌套配置值"""
    config = _load()
    value = config
    for key in keys:
        value = value[key]
    return value

# 应用信息
APP_ID = _get(['feishu_config', 'app_info', 'APP_ID'])
APP_SECRET = _get(['feishu_config', 'app_info', 'APP_SECRET'])
BOT_WEBHOOK = _get(['feishu_config', 'bot_webhook'])

# 表格信息
BASE_TOKEN = _get(['tables', 'base_token'])
TABLE_DY_ACCOUNTS = _get(['tables', 'douyin', 'accounts'])
TABLE_DY_NOTES = _get(['tables', 'douyin', 'notes'])
TABLE_XHS_ACCOUNTS = _get(['tables', 'xiaohongshu', 'accounts'])
TABLE_XHS_NOTES = _get(['tables', 'xiaohongshu', 'notes'])