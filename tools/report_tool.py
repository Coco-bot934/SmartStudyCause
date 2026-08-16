import os
import re
import io
import json
import base64
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import requests
from flask import Flask, request, render_template_string, send_file, redirect, url_for, flash
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
API_PY = ROOT / "z_扣子api.py"

app = Flask(__name__)
app.secret_key = os.environ.get("REPORT_TOOL_SECRET", "dev-secret")

UPLOAD_FORM = """
<!doctype html>
<title>Generate Exam Report</title>
<h2>Upload exam images (one or more), template, and prompt</h2>
<form method=post enctype=multipart/form-data action="/generate">
  Prompt (instructions to the agent):<br>
  <textarea name=prompt rows=6 cols=80></textarea><br><br>
  Exam images: <input type=file name=images multiple><br><br>
  Template (optional, docx): <input type=file name=template><br><br>
  Use async endpoint? <input type=checkbox name=async value=1><br><br>
  <input type=submit value=Generate>
</form>
"""


def parse_config_from_source(path: Path) -> Dict[str, Any]:
    """Try to extract useful API config from the example file without executing it."""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    cfg: Dict[str, Any] = {}

    m = re.search(r"https?://[\w\-._/~:%?#@!$&'()*+,;=]+", text)
    if m:
        cfg.setdefault("url", m.group(0))

    m2 = re.search(r"Authorization\s*:\s*\"Bearer\s*([^\"]+)\"", text)
    if m2:
        cfg.setdefault("auth_token", m2.group(1))

    m3 = re.search(r"\"project_id\"\s*:\s*\"([0-9a-zA-Z_-]+)\"", text)
    if m3:
        cfg.setdefault("project_id", m3.group(1))

    m4 = re.search(r"\"session_id\"\s*:\s*\"([^\"]+)\"", text)
    if m4:
        cfg.setdefault("session_id", m4.group(1))

    # try to extract a system prompt or tools listing if present in the example
    m5 = re.search(r"system_prompt\s*[:=]\s*\"([\s\S]*?)\"", text)
    if m5:
        cfg.setdefault("system_prompt", m5.group(1))
    m6 = re.search(r"\"system\"\s*:\s*\{([\s\S]*?)\}", text)
    if m6:
        cfg.setdefault("system_def", m6.group(1))

    return cfg


def build_payload(prompt: str, images: List[bytes], image_names: List[str], template_bytes: bytes | None, template_name: str | None,
                 project_id: str | None = None, session_id: str | None = None) -> Dict:
    # Build payload in the same structure as the example Coze agent `stream_run` endpoint.
    # Use the array-format prompt that the live agent expects: a list of items
    # each item is like {"type":"text","content":{"text":"..."}} or
    # {"type":"upload_file","content":{"upload_file": {"url":"...","file_name":"..."}}}
    prompt_items = [{"type": "text", "content": {"text": prompt}}]

    for name, b in zip(image_names, images):
        data_url = "data:image/jpeg;base64," + base64.b64encode(b).decode('ascii')
        prompt_items.append({
            "type": "upload_file",
            "content": {"upload_file": {"url": data_url, "file_name": name}}
        })

    if template_bytes and template_name:
        file_data = "data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64," + base64.b64encode(template_bytes).decode('ascii')
        prompt_items.append({
            "type": "upload_file",
            "content": {"upload_file": {"url": file_data, "file_name": template_name}}
        })

    payload = {
        "content": {
            "query": {
                "prompt": prompt_items
            }
        },
        "type": "query",
    }
    if project_id:
        payload["project_id"] = project_id
    if session_id:
        payload["session_id"] = session_id
    return payload


def _extract_text_candidates(value):
    """Recursively collect likely text payloads from nested Coze event JSON."""
    collected = []
    if value is None:
        return collected
    if isinstance(value, str):
        s = value.strip()
        if s and len(s) > 2:
            collected.append(s)
        return collected
    if isinstance(value, list):
        for item in value:
            collected.extend(_extract_text_candidates(item))
        return collected
    if isinstance(value, dict):
        for key, item in value.items():
            key_l = str(key).lower()
            if key_l in {"session_id", "project_id", "id", "conversation_id", "tool_call_id", "bot_id", "chat_id", "created_at", "updated_at", "meta_data", "reasoning_content"}:
                continue
            if isinstance(item, (str, list, dict)):
                collected.extend(_extract_text_candidates(item))
        return collected
    return collected


def call_agent_api(url: str, token: str | None, payload: Dict, stream: bool = True) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print("===== Coze request debug =====")
    print("URL:", url)
    # mask Authorization when printing logs to avoid leaking tokens
    auth = headers.get("Authorization")
    if auth:
        masked = auth[:12] + "...[REDACTED]"
    else:
        masked = "(missing)"
    print("Authorization (masked):", masked)
    print("Authorization present:", bool(auth))
    # print other headers without Authorization to reduce accidental leaks
    other_headers = {k: v for k, v in headers.items() if k.lower() != "authorization"}
    print("HEADERS (others):", other_headers)
    print("PAYLOAD:", json.dumps(payload, ensure_ascii=False, indent=2))

    try:
        # prepare the request to inspect the final headers sent over the wire
        session = requests.Session()
        req = requests.Request('POST', url, headers=headers, json=payload)
        prepared = session.prepare_request(req)
        print("Prepared request headers:", dict(prepared.headers))
        resp = session.send(prepared, stream=stream, timeout=120)
    except Exception as e:
        return {"error": f"request failed: {e}"}

    print("===== Coze response debug =====")
    print("status:", resp.status_code)
    print("content-type:", resp.headers.get("content-type"))
    print("raw response headers:", dict(resp.headers))

    if stream:
        collected = []
        seen_any = False

        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            line = line.strip()
            print("raw stream line:", line)
            if line.startswith("data:"):
                data_text = line[5:].strip()
            elif line.startswith("event:"):
                continue
            else:
                continue

            if not data_text:
                continue
            seen_any = True

            try:
                parsed = json.loads(data_text)
            except Exception:
                s = data_text.strip()
                if s:
                    collected.append(s)
                continue

            current = parsed
            if isinstance(current, dict) and isinstance(current.get("data"), str):
                try:
                    current = json.loads(current["data"])
                except Exception:
                    current = current["data"]
            if isinstance(current, dict) and isinstance(current.get("content"), str):
                collected.append(current["content"])

            candidates = _extract_text_candidates(current)
            if candidates:
                collected.extend(candidates)

        print("collected candidates:", collected)
        text = "\n".join(dict.fromkeys(part.strip() for part in collected if part and part.strip()))
        if not text:
            if not seen_any:
                return {"ok": True, "text": ""}
            return {"ok": True, "text": ""}

        print("final parsed text:", text)
        try:
            parsed = json.loads(text)
            return {"ok": True, "data": parsed}
        except Exception:
            return {"ok": True, "text": text}
    else:
        body = resp.text
        print("non-stream body:", body)
        ctype = resp.headers.get("content-type", "")
        if "application/json" in ctype or body.strip().startswith("{"):
            try:
                return {"ok": True, "data": resp.json()}
            except Exception:
                return {"ok": True, "text": body}
        else:
            return {"ok": True, "binary": resp.content, "content_type": ctype}


def json_to_docx(data: Dict[str, Any]) -> bytes:
    doc = Document()
    doc.add_heading("试卷分析报告", level=1)
    def render(obj, parent=None):
        if isinstance(obj, dict):
            for k, v in obj.items():
                doc.add_heading(str(k), level=2)
                render(v)
        elif isinstance(obj, list):
            for i, item in enumerate(obj, 1):
                doc.add_paragraph(f"{i}. ")
                render(item)
        else:
            doc.add_paragraph(str(obj))

    render(data)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


@app.route("/", methods=["GET"])
def index():
    return render_template_string(UPLOAD_FORM)


@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("prompt", "请分析上传的试卷并产出详细报告。")
    use_async = bool(request.form.get("async"))

    images = []
    image_names = []
    for f in request.files.getlist("images"):
        if f and f.filename:
            b = f.read()
            images.append(b)
            image_names.append(f.filename)

    template_bytes = None
    template_name = None
    t = request.files.get("template")
    if t and t.filename:
        template_bytes = t.read()
        template_name = t.filename

    cfg = parse_config_from_source(API_PY)
    url = cfg.get("url") or os.environ.get("COZE_API_URL")
    token = cfg.get("auth_token") or os.environ.get("COZE_API_TOKEN")

    if not url:
        flash("无法从 z_扣子api.py 自动检测 API URL，请设置 COZE_API_URL 环境变量或在 z_扣子api.py 中添加 URL。")
        return redirect(url_for("index"))

    payload = build_payload(prompt, images, image_names, template_bytes, template_name)

    # prefer stream_run endpoint; if async checkbox set try async_run
    if use_async and url.endswith("stream_run"):
        url = url.replace("stream_run", "async_run")

    result = call_agent_api(url, token, payload, stream=True)

    if result.get("error"):
        flash(result["error"]) 
        return redirect(url_for("index"))

    # If binary docx returned
    if result.get("binary"):
        b = result["binary"]
        return send_file(io.BytesIO(b), as_attachment=True, download_name="report.docx", mimetype=result.get("content_type","application/octet-stream"))

    # If JSON data present, convert to docx
    data = result.get("data") or result.get("text")
    if isinstance(data, dict):
        doc_bytes = json_to_docx(data)
        return send_file(io.BytesIO(doc_bytes), as_attachment=True, download_name="report.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        # fallback: return text as plain file
        text = result.get("text") or json.dumps(result, ensure_ascii=False, indent=2)
        return send_file(io.BytesIO(text.encode("utf-8")), as_attachment=True, download_name="report.txt", mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)), debug=True)
