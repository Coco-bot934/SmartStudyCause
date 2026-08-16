import tools.report_tool as rt
import base64

class FakeResp:
    def __init__(self):
        self.status_code = 200
        self.headers = {"content-type": "text/event-stream"}
        self.content = b""
    def iter_lines(self, decode_unicode=True):
        # simulate SSE lines with nested JSON strings
        yield 'data: {"event":"conversation.message.delta","data":"{\\"content\\":\\"{\\\\\\"report\\\\\\":\\\\\\"学生表现良好\\\\\\",\\\\\\"score\\\\\\":95}\\"}"}'
        yield 'data: {"event":"conversation.chat.completed","data":"{\\"status\\":\\"completed\\"}"}'

orig_post = rt.requests.post
try:
    rt.requests.post = lambda *args, **kwargs: FakeResp()

    img = b"\xff\xd8\xfffakejpeg"
    payload = rt.build_payload("请分析这张试卷", [img], ["exam.jpg"], None, None)
    print("=== Test payload ===")
    print(payload)
    res = rt.call_agent_api("http://example.com/stream_run", "token-abc", payload, stream=True)
    print("=== Result ===")
    print(res)
finally:
    rt.requests.post = orig_post
