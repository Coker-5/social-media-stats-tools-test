import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from typing import Dict, List, Any
from tools.logstar import get_logger
from tools.config_loader import (APP_ID, APP_SECRET, DEVELOPERS_ID_LIST, BOT_WEBHOOK)
from tools.send_feishu import FeishuBot

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)

class FeishuBitableWriter:
    def __init__(self, base_token: str, table_id: str):
        self.base_token = base_token
        self.table_id = table_id
        self.client = lark.Client.builder() \
            .app_id(APP_ID) \
            .app_secret(APP_SECRET) \
            .log_level(lark.LogLevel.INFO) \
            .build()

    def _send_exception_alert(self, error_message: str):
        """发送异常告警"""
        try:
            bot.send_card_alert(
                title="爬虫",
                task_name="爬虫计划任务运行「异常」时告警-新媒体数据-刘建强",
                run_script_name=__file__,
                exception_plan="爬虫-新媒体数据-刘建强",
                exception_app="飞书多维表格",
                error_message=error_message,
                client_ip="10.30.40.150",
                at_all=False,
                at_user_ids=DEVELOPERS_ID_LIST
            )
        except Exception as alert_e:
            log.error(f"发送告警失败: {alert_e}")

    def add_records(self, data_list: List[Dict[str, Any]]):
        """
        使用 SDK 批量添加记录到多维表格
        """
        if not data_list:
            return

        # 统一格式为列表
        if isinstance(data_list, dict):
            data_list = [data_list]

        # 转换数据格式为 SDK 要求的 AppTableRecord 对象
        records = []
        for item in data_list:
            if not isinstance(item, dict):
                continue
            # 过滤掉 None 值，避免 SDK 校验失败
            fields = {k: v for k, v in item.items() if v is not None}
            if fields:
                records.append(AppTableRecord.builder().fields(fields).build())

        if not records:
            log.warning("没有有效数据需要写入")
            return

        # 构造批量创建请求
        # 注意：batch_create 单次最大支持 500 条
        request = BatchCreateAppTableRecordRequest.builder() \
            .app_token(self.base_token) \
            .table_id(self.table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder()
                          .records(records)
                          .build()) \
            .build()

        # 发起请求
        response = self.client.bitable.v1.app_table_record.batch_create(request)

        # 处理响应
        if not response.success():
            error_msg = f"SDK 批量写入失败: code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
            log.error(error_msg)
            self._send_exception_alert(error_msg)
            return