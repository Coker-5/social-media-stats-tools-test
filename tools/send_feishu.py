# feishu_webhook.py

import requests
import json


class FeishuBot:
    """飞书机器人Webhook"""

    def __init__(self, webhook_url: str):
        """
        初始化Webhook
        :param webhook_url: 飞书机器人的Webhook地址
        """
        self.webhook_url = webhook_url

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
        requests.post(
            self.webhook_url,
            headers=headers,
            data=json.dumps(message, ensure_ascii=False).encode('utf-8'),
            timeout=10
        )




# 使用示例
if __name__ == "__main__":
    # 你的飞书机器人Webhook地址
    # 格式类似：https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    WEBHOOK_URL = "你的飞书机器人Webhook地址"

    # 创建Webhook实例
    bot = FeishuBot(WEBHOOK_URL)

    # 发送简单的文本消息
    bot.send_text("你好，这是通过Webhook发送的测试消息！")

    # 发送@所有人的消息
    bot.send_text("紧急通知：系统出现异常！", at_all=True)

    # 发送@特定用户的消息（需要用户ID）
    bot.send_text("提醒：您有新的任务需要处理", at_user_ids=["ou_1234567890"])