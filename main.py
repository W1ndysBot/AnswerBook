# script/AnswerBook/main.py

import logging
import os
import sys
import re
import json
import aiohttp

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import *
from app.api import send_group_msg, send_private_msg
from app.switch import load_switch, save_switch


# 数据存储路径，实际开发时，请将AnswerBook替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "AnswerBook",
)


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "AnswerBook")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "AnswerBook", status)


# 处理开关状态
async def toggle_function_status(websocket, group_id, message_id, authorized):
    if not authorized:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]❌❌❌你没有权限对AnswerBook功能进行操作,请联系管理员。",
        )
        return

    if load_function_status(group_id):
        save_function_status(group_id, False)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]🚫🚫🚫AnswerBook功能已关闭",
        )
    else:
        save_function_status(group_id, True)
        await send_group_msg(
            websocket,
            group_id,
            f'[CQ:reply,id={message_id}]✅✅✅AnswerBook功能已开启，输入"答案卷卷+问题"即可与神秘的卷卷之书对话',
        )


# 异步请求答案之书API
async def request_answer_book(question):
    """异步请求答案之书API"""
    try:
        url = f"https://v2.xxapi.cn/api/answers"
        params = {"question": question}
        headers = {"User-Agent": "xiaoxiaoapi/1.0.0 (https://xxapi.cn)"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                return await response.json()
    except Exception as e:
        logging.error(f"请求答案之书API失败: {e}")
        return {"code": 500, "msg": f"请求答案之书API失败: {str(e)}"}


# 群消息处理函数
async def handle_group_message(websocket, msg):
    """处理群消息"""
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        message_id = str(msg.get("message_id"))
        authorized = user_id in owner_id

        # 处理开关命令
        if raw_message.lower() == "ab":
            await toggle_function_status(websocket, group_id, message_id, authorized)
            return
        # 检查功能是否开启
        if load_function_status(group_id):
            if raw_message.startswith("答案卷卷"):
                question = raw_message[4:]
                answer = await request_answer_book(question)
                if answer.get("code") == 200:
                    # 格式化完整的返回数据
                    data = answer.get("data", {})
                    formatted_response = f"""
{data.get('title_zh', '')}
{data.get('description_zh', '')}
{data.get('title_en', '')}
{data.get('description_en', '')}"""
                    await send_group_msg(
                        websocket,
                        group_id,
                        f"[CQ:reply,id={message_id}]{formatted_response}",
                    )
                else:
                    await send_group_msg(
                        websocket, group_id, answer.get("msg", "请求失败")
                    )
    except Exception as e:
        logging.error(f"处理AnswerBook群消息失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理AnswerBook群消息失败，错误信息：" + str(e),
        )
        return


# 私聊消息处理函数
async def handle_private_message(websocket, msg):
    """处理私聊消息"""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        raw_message = str(msg.get("raw_message"))
        # 私聊消息处理逻辑
        pass
    except Exception as e:
        logging.error(f"处理AnswerBook私聊消息失败: {e}")
        await send_private_msg(
            websocket,
            msg.get("user_id"),
            "处理AnswerBook私聊消息失败，错误信息：" + str(e),
        )
        return


# 群通知处理函数
async def handle_group_notice(websocket, msg):
    """处理群通知"""
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        notice_type = str(msg.get("notice_type"))
        operator_id = str(msg.get("operator_id", ""))

    except Exception as e:
        logging.error(f"处理AnswerBook群通知失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理AnswerBook群通知失败，错误信息：" + str(e),
        )
        return


# 回应事件处理函数
async def handle_response(websocket, msg):
    """处理回调事件"""
    try:
        echo = msg.get("echo")
        if echo and echo.startswith("xxx"):
            # 回调处理逻辑
            pass
    except Exception as e:
        logging.error(f"处理AnswerBook回调事件失败: {e}")
        await send_group_msg(
            websocket,
            msg.get("group_id"),
            f"处理AnswerBook回调事件失败，错误信息：{str(e)}",
        )
        return


# 请求事件处理函数
async def handle_request_event(websocket, msg):
    """处理请求事件"""
    try:
        request_type = msg.get("request_type")
        pass
    except Exception as e:
        logging.error(f"处理AnswerBook请求事件失败: {e}")
        return


# 统一事件处理入口
async def handle_events(websocket, msg):
    """统一事件处理入口"""
    post_type = msg.get("post_type", "response")  # 添加默认值
    try:
        # 这里可以放一些定时任务，在函数内设置时间差检测即可

        # 处理回调事件，用于一些需要获取ws返回内容的事件
        if msg.get("status") == "ok":
            await handle_response(websocket, msg)
            return

        post_type = msg.get("post_type")

        # 处理元事件，每次心跳时触发，用于一些定时任务
        if post_type == "meta_event":
            pass

        # 处理消息事件，用于处理群消息和私聊消息
        elif post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await handle_group_message(websocket, msg)
            elif message_type == "private":
                await handle_private_message(websocket, msg)

        # 处理通知事件，用于处理群通知
        elif post_type == "notice":
            await handle_group_notice(websocket, msg)

        # 处理请求事件，用于处理请求事件
        elif post_type == "request":
            await handle_request_event(websocket, msg)

    except Exception as e:
        error_type = {
            "message": "消息",
            "notice": "通知",
            "request": "请求",
            "meta_event": "元事件",
        }.get(post_type, "未知")

        logging.error(f"处理AnswerBook{error_type}事件失败: {e}")

        # 发送错误提示
        if post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await send_group_msg(
                    websocket,
                    msg.get("group_id"),
                    f"处理AnswerBook{error_type}事件失败，错误信息：{str(e)}",
                )
            elif message_type == "private":
                await send_private_msg(
                    websocket,
                    msg.get("user_id"),
                    f"处理AnswerBook{error_type}事件失败，错误信息：{str(e)}",
                )
