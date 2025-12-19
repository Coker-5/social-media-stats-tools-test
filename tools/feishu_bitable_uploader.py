# feishu_bitable_writer.py

import requests
import json
from typing import Dict, List, Any
from tools.logstar import get_logger
from tools.config_loader import (APP_ID, APP_SECRET, USER_IDS, BOT_WEBHOOK)
from tools.send_feishu import FeishuBot

log = get_logger()
bot = FeishuBot(BOT_WEBHOOK)


class FeishuBitableWriter:
    def __init__(self, base_token: str, table_id: str):
        self.app_id = APP_ID
        self.app_secret = APP_SECRET
        self.base_token = base_token
        self.table_id = table_id
        self.tenant_access_token = None
        self._get_tenant_access_token()

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
                at_user_ids=[USER_IDS.get("刘建强", "")]
            )
        except Exception as alert_e:
            log.error(f"发送告警失败: {alert_e}")
            raise

    def _get_tenant_access_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        try:
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                error_msg = f"Failed to get tenant_access_token: {data}"
                log.error(error_msg)
                self._send_exception_alert(error_msg)
                raise Exception(error_msg)
            self.tenant_access_token = data["tenant_access_token"]
        except Exception as e:
            error_msg = f"获取tenant_access_token失败: {e}"
            log.error(error_msg)
            self._send_exception_alert(error_msg)
            raise

    def _build_record_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建飞书记录字段
        直接使用data的key作为飞书字段名
        """
        # 允许飞书支持的字段类型，包括字典（用于超链接等）
        allowed_types = (str, int, float, bool, dict)
        return {
            k: v for k, v in data.items()
            if isinstance(v, allowed_types) or v is None
        }

    def add_records(self, data_list: List[Dict[str, Any]]):
        """
        批量添加记录到飞书多维表格
        :param data_list: 要写入的数据列表，字典的key必须等于飞书字段名
        """
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_token}/tables/{self.table_id}/records"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # 确保传入的是列表类型
        if not isinstance(data_list, list):
            # 如果是单个字典，转换为列表
            if isinstance(data_list, dict):
                data_list = [data_list]
            else:
                error_msg = f"❌ 传入的数据必须是字典或字典列表，实际类型是: {type(data_list)}"
                log.error(error_msg)
                self._send_exception_alert(error_msg)
                return

        for data in data_list:
            # 确保每个元素是字典类型
            if not isinstance(data, dict):
                error_msg = f"❌ 跳过非字典类型的数据: {type(data)}"
                log.error(error_msg)
                self._send_exception_alert(error_msg)
                continue

            fields = self._build_record_fields(data)
            if not fields:
                log.info("⚠️ 保存数据时跳过一条空记录")
                continue

            payload = {"fields": fields}
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(payload, ensure_ascii=False).encode('utf-8')
                )
                resp.raise_for_status()
                resp_data = resp.json()

                if resp_data.get("code") != 0:
                    error_msg = f"写入多维表格 {self.table_id} 失败: {payload['fields']}，因为：{resp.text}"
                    log.error(f"❌ {error_msg}")
                    self._send_exception_alert(error_msg)
            except Exception as e:
                error_msg = f"请求失败: {e}"
                log.error(f"❌ {error_msg}")
                self._send_exception_alert(error_msg)
                raise
