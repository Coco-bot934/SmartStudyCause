"""
示例：从环境变量读取 Coze agent endpoint 和 token，然后 POST 执行并打印 SSE 流中的 data 行。

环境变量：
  COZE_API_URL   - API endpoint, e.g. https://h4xjs2w6vd.coze.site/stream_run
  COZE_API_TOKEN - Bearer token for Authorization
  COZE_PROJECT_ID - （可选）project_id 用于 payload

使用方式（Windows PowerShell 示例）：
  setx COZE_API_URL "https://your.coze.site/stream_run"
  setx COZE_API_TOKEN "your_actual_token"
  # 重新打开终端后运行
  python z_扣子api.py
"""

import os
import sys
import json
import requests


def get_env(name: str) -> str:
    return os.environ.get(name, "")


def make_headers(token: str) -> dict:
    h = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def build_payload(prompt_text: str, project_id: str | None = None, session_id: str | None = None) -> dict:
    payload = {
        "content": {
            "query": {
                "prompt": [
                    {"type": "text", "content": {"text": prompt_text}}
                ]
            }
        },
        "type": "query",
    }
    if session_id:
        payload["session_id"] = session_id
    if project_id:
        payload["project_id"] = project_id
    return payload


def stream_run(url: str, headers: dict, payload: dict):
    print("POST ->", url)
    resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=120)
    print("status:", resp.status_code)
    try:
        resp.raise_for_status()
    except Exception:
        print("Response body:\n", resp.text)
        raise

    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        if isinstance(line, bytes):
            try:
                line = line.decode('utf-8')
            except Exception:
                line = str(line)
        if line.startswith("data:"):
            data_text = line[5:].strip()
            try:
                parsed = json.loads(data_text)
                print(json.dumps(parsed, ensure_ascii=False, indent=2))
            except Exception:
                print(data_text)


def main():
    url = get_env("COZE_API_URL")
    token = get_env("COZE_API_TOKEN")
    project_id = get_env("COZE_PROJECT_ID")

    if not url or not token:
        print("错误：未检测到 COZE_API_URL 或 COZE_API_TOKEN 环境变量。")
        print("请在终端设置后重新运行。示例 (PowerShell):")
        print("  setx COZE_API_URL \"https://your.coze.site/stream_run\"")
        print("  setx COZE_API_TOKEN \"your_actual_token\"")
        print("注意：setx 在新打开的终端生效；如果只想在当前会话临时设置，请使用: $env:COZE_API_TOKEN='token'")
        sys.exit(1)

    prompt = "请分析以下试卷图片并输出结构化报告：\n（这是一个测试请求，不包含实际图片）"
    payload = build_payload(prompt, project_id=project_id, session_id=None)
    headers = make_headers(token)

    stream_run(url, headers, payload)


if __name__ == "__main__":
    main()