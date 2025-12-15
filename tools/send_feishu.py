# feishu_webhook.py
import time
from typing import List, Dict, Any, Optional
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

    # 发送卡片
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
            at_all: bool = False,at_user_ids: List[str] = None,at_mobiles: List[str] = None
    ) -> Dict[str, Any]:
        """
        发送监控告警消息（卡片格式）

        :param task_name: 任务名称
        :param run_script_name: 运行脚本名称
        :param exception_plan: 异常计划
        :param exception_app: 异常应用
        :param error_message: 错误信息
        :param client_ip: 客户端IP
        :param error_id: 可选错误ID（根据图片信息可能有）
        :param at_all: 是否@所有人
        :param at_user_ids: 要@的用户ID列表
        :param at_mobiles: 要@的手机号列表
        :return: 返回响应结果
        """
        # 自动生成当前时间，格式为YYYY-MM-DD HH:MM:SS
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        full_error_message = error_message

        # 构建卡片消息
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True  # 启用宽屏模式
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"⚠️ {title}监控告警"
                    },
                    "template": title_color  # 红色表示异常/告警
                },
                "elements": []
            }
        }

        # 添加任务名称
        card["card"]["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**任务名称**：{task_name}"
            }
        })

        # 添加运行时间（自动填充当前时间）
        card["card"]["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**运行时间**：{current_time}"
            }
        })

        # 添加运行脚本名称
        if run_script_name:
            card["card"]["elements"].append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**运行脚本名称**：{run_script_name}"
                }
            })

        # 添加异常计划
        card["card"]["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**异常计划**：{exception_plan}"
            }
        })

        # 添加异常应用
        card["card"]["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**异常应用**：{exception_app}"
            }
        })

        # 添加错误信息
        card["card"]["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**错误信息**：\n{full_error_message}"
            }
        })

        # 添加分隔线
        card["card"]["elements"].append({
            "tag": "hr"
        })

        # 添加客户端IP
        if client_ip:
            card["card"]["elements"].append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**客户端 IP**：{client_ip}"
                }
            })


        # 处理@功能 - 在飞书卡片消息中正确的方式
        if at_all or at_user_ids or at_mobiles:
            # 创建一个专门的div来包含@信息
            at_content = "**告警通知**："

            if at_all:
                at_content += "<at id=all></at> "
            elif at_user_ids:
                for user_id in at_user_ids:
                    at_content += f"<at id={user_id}></at> "
            elif at_mobiles:
                for mobile in at_mobiles:
                    at_content += f"<at phone_number={mobile}></at> "

            # 添加@信息的div
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


# 使用示例
if __name__ == "__main__":
    # 你的飞书机器人Webhook地址
    WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/76a6c534-6069-4e1b-b6af-49acd1d2fdc8"

    # 创建Webhook实例
    bot = FeishuBot(WEBHOOK_URL)



    # 测试2：发送卡片消息（带@功能）- 注意需要正确的用户ID
    result2 = bot.send_card_alert(
        title="爬虫",
        title_color="yellow",
        task_name="爬虫计划任务运行「异常」时告警-新媒体数据-刘建强",
        run_script_name="send_feishu.py",
        exception_plan="爬虫-新媒体数据-刘建强",
        exception_app="小红书创作者中心",
        error_message="任务失败，在【市场排行-店铺】中第26行:出错:Message:未找到元素，元素名:svg;",
        client_ip="10.30.40.150",
        at_all=False,
        at_user_ids=["ou_cf1e39d175637648419f781542ea1ffa"]  # 替换为实际的用户ID
    )
    print(f"发送结果2（带@）: {result2}")

    # 测试3：发送文本消息测试@功能
    result3 = bot.send_text(
        text="这是一个测试消息",
        at_user_ids=["ou_cf1e39d175637648419f781542ea1ffa"]  # 用文本消息测试@功能
    )
    print(f"文本消息发送结果: {result3}")

