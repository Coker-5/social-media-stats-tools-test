import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from typing import Dict, List, Any
from tools.logstar import get_logger

log = get_logger()


class FeishuBitableWriter:
    def __init__(self, app_id: str, app_secret: str, base_token: str, table_id: str, bot=None, developers=None):
        """
        多维表格写入器
        """
        self.base_token = base_token
        self.table_id = table_id
        self.bot = bot  # 传入的 FeishuBot 实例
        self.developers = developers

        # 初始化 Lark 客户端
        self.client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .log_level(lark.LogLevel.INFO) \
            .build()

    def _send_exception_alert(self, error_message: str):
        """使用项目专属的机器人发送告警"""
        try:
            self.bot.send_card_alert(
                itle="爬虫",
                task_name="爬虫计划任务运行「异常」时告警-新媒体数据-刘建强",
                run_script_name=__file__,
                exception_plan="爬虫-新媒体数据-刘建强",
                exception_app="飞书多维表格",
                error_message=error_message,
                client_ip="10.30.40.150",
                at_all=False,
                at_user_ids=self.developers
            )
        except Exception as alert_e:
            log.error(f"发送告警失败: {alert_e}")

    def add_records(self, data_list: List[Dict[str, Any]]):
        """批量添加记录"""
        if not data_list:
            return

        if isinstance(data_list, dict):
            data_list = [data_list]

        # 1. 转换格式
        records = []
        for item in data_list:
            if not isinstance(item, dict): continue
            fields = {k: v for k, v in item.items() if v is not None}
            if fields:
                records.append(AppTableRecord.builder().fields(fields).build())


        # 2. 构造请求
        request = BatchCreateAppTableRecordRequest.builder() \
            .app_token(self.base_token) \
            .table_id(self.table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder()
                          .records(records)
                          .build()) \
            .build()

        # 3. 发起请求并处理
        response = self.client.bitable.v1.app_table_record.batch_create(request)

        if not response.success():
            error_msg = f"写入失败: code: {response.code}, msg: {response.msg}"
            log.error(error_msg)
            self._send_exception_alert(error_msg)
            return