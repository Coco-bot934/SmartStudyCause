
"""使用 cozepy 调用 Coze 平台 Bot API 进行试卷分析的工具

该工具通过 Coze 平台的 Bot 来实现试卷分析功能。
使用前需要在 Coze 平台创建一个试卷分析 Bot，并获取 bot_id 和 access_token。

配置方式：
1. 在 Coze 平台 (https://www.coze.cn) 创建 Bot
2. 将试卷分析 Agent 的能力配置到 Bot 中（可以上传试卷分析相关的提示词）
3. 获取 Bot ID 和个人访问令牌 (Personal Access Token)
4. 将配置信息填入本工具的参数或环境变量中
"""
import os
from langchain.tools import tool
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
from cozepy import Coze, TokenAuth, Message, ChatEventType


@tool
def analyze_exam_paper_via_coze(
    image_urls: list[str],
    bot_id: str = "",
    access_token: str = "",
    user_id: str = "exam_analyzer_user",
    base_url: str = ""
) -> str:
    """通过 Coze 平台 Bot API 分析试卷照片并返回分析结果。

    该工具使用 cozepy SDK 调用 Coze 平台的 Bot Chat API，
    将试卷照片发送给 Bot 进行分析，并获取分析结果。

    Args:
        image_urls: 试卷照片的 URL 列表，支持一张或多张照片
        bot_id: Coze 平台 Bot 的 ID。如果为空则从环境变量 COZE_BOT_ID 读取
        access_token: Coze 平台个人访问令牌。如果为空则从环境变量 COZE_ACCESS_TOKEN 读取
        user_id: 用户标识符，用于区分不同用户的对话
        base_url: Coze API 基础 URL。默认为国内版 https://api.coze.cn，
                  如果为空则从环境变量 COZE_BASE_URL 读取

    Returns:
        Bot 返回的试卷分析结果文本

    环境变量配置（可选）：
        - COZE_BOT_ID: Bot ID
        - COZE_ACCESS_TOKEN: 个人访问令牌
        - COZE_BASE_URL: API 基础 URL（默认 https://api.coze.cn）

    示例：
        # 直接传入参数
        result = analyze_exam_paper_via_coze(
            image_urls=["https://example.com/exam1.jpg"],
            bot_id="your_bot_id",
            access_token="your_token"
        )

        # 使用环境变量
        # export COZE_BOT_ID="your_bot_id"
        # export COZE_ACCESS_TOKEN="your_token"
        result = analyze_exam_paper_via_coze(
            image_urls=["https://example.com/exam1.jpg"]
        )
    """
    ctx = request_context.get() or new_context(method="analyze_exam_paper_via_coze")

    # 从参数或环境变量获取配置
    actual_bot_id = bot_id or os.getenv("COZE_BOT_ID", "")
    actual_access_token = access_token or os.getenv("COZE_ACCESS_TOKEN", "")
    actual_base_url = base_url or os.getenv("COZE_BASE_URL", "https://api.coze.cn")

    if not actual_bot_id:
        return "错误：未提供 bot_id 参数，也未设置 COZE_BOT_ID 环境变量"
    if not actual_access_token:
        return "错误：未提供 access_token 参数，也未设置 COZE_ACCESS_TOKEN 环境变量"
    if not image_urls:
        return "错误：请提供至少一张试卷照片的 URL"

    try:
        # 初始化 Coze 客户端
        auth = TokenAuth(token=actual_access_token)
        coze_client = Coze(auth=auth, base_url=actual_base_url)

        # 构建消息内容：包含文本提示和图片
        message_objects = []
        for img_url in image_urls:
            message_objects.append(
                MessageObjectString(type=MessageObjectStringType.IMAGE, file_url=img_url)
            )

        # 添加分析指令
        analysis_prompt = "请仔细分析这些试卷照片，识别所有题目、学生作答、老师批改标记和得分情况。然后按照以下格式输出分析报告：\n\n1. 试卷基本信息（科目、年级、得分等）\n2. 各题型失分情况统计\n3. 每道错题的失分原因分析\n4. 知识点掌握情况评估\n5. 后续学习建议"
        message_objects.insert(0, MessageObjectString(type=MessageObjectStringType.TEXT, text=analysis_prompt))

        # 构建用户消息
        user_message = Message.build_user_question_objects(objects=message_objects)

        # 调用 Bot Chat API（流式）
        response_text = ""
        for event in coze_client.chat.stream(
            bot_id=actual_bot_id,
            user_id=user_id,
            additional_messages=[user_message]
        ):
            if event is None:
                continue

            if event.event in (
                ChatEventType.CONVERSATION_MESSAGE_DELTA,
                ChatEventType.CONVERSATION_MESSAGE_COMPLETED,
            ):
                message = getattr(event, "message", None)
                if message is None:
                    continue

                # 兼容 content 直接为字符串、JSON 字符串、object-string 结构等
                content = getattr(message, "content", None)
                if isinstance(content, str) and content:
                    response_text += content
                elif isinstance(content, (dict, list)):
                    response_text += json.dumps(content, ensure_ascii=False)
                else:
                    try:
                        payload = message.model_dump()
                    except Exception:
                        payload = {}
                    if isinstance(payload, dict):
                        def walk(value, out):
                            if isinstance(value, str):
                                s = value.strip()
                                if s and len(s) > 2:
                                    out.append(s)
                            elif isinstance(value, list):
                                for item in value:
                                    walk(item, out)
                            elif isinstance(value, dict):
                                for k, v in value.items():
                                    if str(k).lower() in {"session_id", "project_id", "id", "conversation_id", "bot_id", "chat_id", "created_at", "updated_at"}:
                                        continue
                                    walk(v, out)
                        parts = []
                        walk(payload, parts)
                        if parts:
                            response_text += "\n".join(dict.fromkeys(parts))

            elif event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                break
            elif event.event == ChatEventType.ERROR:
                return f"错误：Coze API 返回错误 - {event}"

        if not response_text:
            return "未获取到分析结果，请检查 Bot 配置或重试"

        return response_text

    except Exception as e:
        return f"调用 Coze API 失败: {str(e)}"


# 导入需要的类型
from cozepy.chat import MessageObjectString, MessageObjectStringType