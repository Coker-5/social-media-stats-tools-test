import json
import sys
from pathlib import Path

def get_project_root():
    """获取项目根目录"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent

_CONFIG_PATH = get_project_root() / "config" / "config.json"

def load_config():
    """读取整个 JSON 字典"""
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(f"配置文件未找到: {_CONFIG_PATH}")
    with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_all_projects():
    """获取所有启用的项目列表"""
    config = load_config()
    projects = config.get("projects", {})
    return {name: cfg for name, cfg in projects.items() if cfg.get("enabled", True)}

def get_project_config(project_name):
    """
    获取单个项目的配置
    :param project_name: 项目名称
    """
    projects = get_all_projects()
    if project_name not in projects:
        raise ValueError(f"项目 '{project_name}' 不存在或未启用，请检查 config.json")
    return projects[project_name]


def extract_user_ids(user_ids_dict, group_name='operations'):
    """工具函数：从单个项目的 user_ids 中提取 ID 列表"""
    if not user_ids_dict or group_name not in user_ids_dict:
        return []
    return [list(d.values())[0] for d in user_ids_dict[group_name] if d]