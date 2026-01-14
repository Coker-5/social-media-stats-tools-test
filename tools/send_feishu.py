# feishu_webhook.py
import time
from typing import List, Dict, Any, Optional
import requests
import json
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
import io
from tools.logstar import get_logger

log = get_logger()


class FeishuBot:
    """飞书机器人Webhook"""

    def __init__(self, webhook_url: str, app_id: str = None, app_secret: str = None):
        self.webhook_url = webhook_url
        # 初始化飞书 Client，它会自动处理 tenant_access_token
        self.client = None
        if app_id and app_secret:
            self.client = lark.Client.builder() \
                .app_id(app_id) \
                .app_secret(app_secret) \
                .log_level(lark.LogLevel.ERROR) \
                .build()


    def upload_image_and_get_key(self, image_bytes: bytes) -> Optional[str]:
        """使用官方 SDK 上传图片"""
        if not self.client:
            log.error("未配置 app_id/app_secret，无法使用上传功能")
            return None

        # 构造请求对象
        request: CreateImageRequest = CreateImageRequest.builder() \
            .request_body(CreateImageRequestBody.builder()
                          .image_type("message")
                          .image(io.BytesIO(image_bytes))  # SDK 接受文件流
                          .build()) \
            .build()

        # 发起请求
        response: CreateImageResponse = self.client.im.v1.image.create(request)

        # 处理响应
        if not response.success():
            log.error(
                f"SDK 上传图片失败: origin={image_bytes}, code={response.code}, error={response.error}, msg={response.msg},")
            return None

        return response.data.image_key


    # 发送文本
    def send_text(self, text: str, at_all: bool = False, at_user_ids: list = None, at_mobiles: list = None):
        """
        发送文本消息
        :param text: 要发送的文本内容
        :param at_all: 是否@所有人
        :param at_user_ids: 要@的用户ID列表
        :param at_mobiles: 要@的手机号列表
        """
        # 构建消息体
        message_text = text

        # 处理@功能
        if at_all:
            # 在文本开头添加@所有人的标签
            message_text = f"<at user_id=\"all\">所有人</at>\n{message_text}"

        elif at_user_ids:
            for user_id in at_user_ids:
                # 添加@特定用户的标签
                message_text += f"\n<at user_id=\"{user_id}\"></at>"

        elif at_mobiles:
            for mobile in at_mobiles:
                # 添加@手机号的标签
                message_text += f"\n<at mobile=\"{mobile}\"></at>"

        # 构建完整的消息
        message = {
            "msg_type": "text",
            "content": {
                "text": message_text
            }
        }

        # 发送请求
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            self.webhook_url,
            headers=headers,
            data=json.dumps(message, ensure_ascii=False).encode('utf-8'),
            timeout=10
        )
        return response.json()

    # 发送失败卡片（支持截图）
    def send_card_alert(
            self,
            title: str,
            title_color: str = "red",
            task_name: str = "",
            run_script_name: str = None,
            exception_plan: str = None,
            exception_app: str = None,
            error_message: str = None,
            client_ip: str = None,
            screenshot_bytes: bytes = None,
            screenshot_text: str = "登录二维码",
            at_all: bool = False,
            at_user_ids: List[str] = None,
            at_mobiles: List[str] = None
    ) -> Dict[str, Any]:
        """
        发送监控告警消息（左右并排布局卡片）
        """
        # 自动生成当前时间
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # 基础卡片配置
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"⚠️ {title}监控告警"
                    },
                    "template": title_color
                },
                "elements": []
            }
        }

        # 1. 构建左侧文字列表
        left_column_elements = []
        left_column_elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"**任务名称**：{task_name}"}
        })
        left_column_elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"**运行时间**：{current_time}"}
        })
        if exception_plan:
            left_column_elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"**异常计划**：{exception_plan}"}
            })
        if exception_app:
            left_column_elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"**异常应用**：{exception_app}"}
            })
        left_column_elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"**错误信息**：\n{error_message}"}
        })

        # 2. 检查是否有图片并尝试上传
        image_key = None
        if screenshot_bytes:
            image_key = self.upload_image_and_get_key(screenshot_bytes)

        # 3. 根据是否有图片，决定是使用并排布局还是垂直布局
        if image_key:
            # 使用分栏布局实现左右并排
            card["card"]["elements"].append({
                "tag": "column_set",
                "flex_mode": "bisect",

                "columns": [
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 4,
                        "elements": left_column_elements
                    },
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,  # 图片栏占 20%
                        "vertical_align": "center",
                        "elements": [
                            {
                                "tag": "img",
                                "img_key": image_key,
                                "mode": "fit_horizontal",
                                "alt": {"tag": "plain_text", "content": "QR"}
                            }
                        ]
                    }
                ]
            })
        else:
            # 如果上传图片失败或没有图片，则回退到普通的垂直显示
            card["card"]["elements"].extend(left_column_elements)

        # 4. 添加分隔线
        card["card"]["elements"].append({"tag": "hr"})

        # 5. 添加客户端 IP
        if client_ip:
            card["card"]["elements"].append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"**客户端 IP**：{client_ip}"}
            })

        # 6. 处理 @ 功能
        if at_all or at_user_ids or at_mobiles:
            at_content = "**告警通知**："
            if at_all:
                at_content += "<at id=all></at> "
            elif at_user_ids:
                for user_id in at_user_ids:
                    at_content += f"<at id={user_id}></at> "
            elif at_mobiles:
                for mobile in at_mobiles:
                    at_content += f"<at phone_number={mobile}></at> "

            card["card"]["elements"].append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": at_content}
            })

        # 发送请求
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(
                self.webhook_url,
                headers=headers,
                data=json.dumps(card, ensure_ascii=False).encode('utf-8'),
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"code": -1, "msg": f"请求失败: {str(e)}"}

    # 发送成功卡片
    def send_card_success(
            self,
            title: str,
            task_name: str = "",
            platform: str = "",
            success_message: str = None,
            at_all: bool = False,
            at_user_ids: List[str] = None,
            at_mobiles: List[str] = None
    ) -> Dict[str, Any]:
        """
        发送监控成功消息

        :param title: 告警标题
        :param task_name: 任务名称
        :param success_message: 成功信息
        :param at_all: 是否@所有人
        :param at_user_ids: 要@的用户ID列表
        :param at_mobiles: 要@的手机号列表
        :return: 返回响应结果
        """
        # 自动生成当前时间
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # 构建卡片消息
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"✅ {title}成功通知"
                    },
                    "template": "green"  # 绿色表示成功
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**任务名称**：{task_name}"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**应用名称**：{platform}"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**完成时间**：{current_time}"
                        }
                    }
                ]
            }
        }

        # 如果有成功信息，则添加
        if success_message:
            card["card"]["elements"].append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**成功信息**：{success_message}"
                }
            })

        # 添加分隔线
        card["card"]["elements"].append({
            "tag": "hr"
        })

        # 处理@功能
        if at_all or at_user_ids or at_mobiles:
            at_content = "**通知**："

            if at_all:
                at_content += "<at id=all></at> "
            elif at_user_ids:
                for user_id in at_user_ids:
                    at_content += f"<at id={user_id}></at> "
            elif at_mobiles:
                for mobile in at_mobiles:
                    at_content += f"<at phone_number={mobile}></at> "

            card["card"]["elements"].append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": at_content
                }
            })

        # 发送请求
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(
                self.webhook_url,
                headers=headers,
                data=json.dumps(card, ensure_ascii=False).encode('utf-8'),
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"code": -1, "msg": f"请求失败: {str(e)}"}
