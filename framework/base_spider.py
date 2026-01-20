import sentry_sdk
from tools.logstar import get_logger
from tools.send_feishu import FeishuBot
from tools.feishu_bitable_uploader import FeishuBitableWriter
from tools.config_loader import extract_user_ids

log = get_logger()

class BaseSpider:
    def __init__(self, tab, project_name, project_config):
        """
        :param tab: DrissionPage 的 Tab 对象
        :param project_name: 项目名称
        :param project_config: 该项目下的完整配置字典
        """
        self.tab = tab
        self.project_name = project_name
        self.config = project_config

        # 快捷访问
        self.tables_config = project_config.get('tables', {})
        self.base_token = self.tables_config.get('base_token')

        # 初始化当前项目专属的飞书机器人
        feishu_cfg = project_config.get('feishu_config', {})
        app_info = feishu_cfg.get('app_info', {})
        self.bot = FeishuBot(
            webhook_url=feishu_cfg.get('bot_webhook'),
            app_id=app_info.get('APP_ID'),
            app_secret=app_info.get('APP_SECRET')
        )

    def save_to_bitable(self, data, config_path):
        """
        保存数据至飞书多维表格
        :param data: 采集到的数据 (dict 或 list)
        :param config_path: 配置文件中 tables 下的路径列表
        """

        target_table_id = self.tables_config
        try:
            for key in config_path:
                target_table_id = target_table_id[key]
        except (KeyError, TypeError):
            log.error(f"[{self.project_name}] 配置寻址失败: 在 tables 中找不到路径 {config_path}")
            return

        feishu_cfg = self.config.get('feishu_config', {})
        app_info = feishu_cfg.get('app_info', {})
        dev_ids = extract_user_ids(self.config.get('user_ids'), 'developers')

        try:
            writer = FeishuBitableWriter(
                app_id=app_info.get('APP_ID'),
                app_secret=app_info.get('APP_SECRET'),
                base_token=self.base_token,
                table_id=target_table_id,
                bot=self.bot,
                developers=dev_ids
            )
            writer.add_records(data)
        except Exception as e:
            log.error(f"[{self.project_name}] 调用飞书多维表格写入器失败: {e}")
            sentry_sdk.capture_exception(e)