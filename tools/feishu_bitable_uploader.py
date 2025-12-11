# feishu_bitable_writer.py

import requests
import json
from typing import Dict, List, Any
from tools.logstar import get_logger
from tools.config_loader import (APP_ID, APP_SECRET)

log = get_logger()


class FeishuBitableWriter:
    def __init__(self, base_token: str, table_id: str):
        self.app_id = APP_ID
        self.app_secret = APP_SECRET
        self.base_token = base_token
        self.table_id = table_id
        self.tenant_access_token = None
        self._get_tenant_access_token()

    def _get_tenant_access_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"Failed to get tenant_access_token: {data}")
        self.tenant_access_token = data["tenant_access_token"]

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
                log.error(f"❌ 传入的数据必须是字典或字典列表，实际类型是: {type(data_list)}")
                return

        for data in data_list:
            # 确保每个元素是字典类型
            if not isinstance(data, dict):
                log.error(f"❌ 跳过非字典类型的数据: {type(data)}")
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
                    log.error(f"❌ 写入失败: {payload['fields']}，因为：{resp.text}")
            except Exception as e:
                log.error(f"❌ 请求失败: {e}")