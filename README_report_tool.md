# Report Tool

Simple Flask tool to upload exam photos and a Word template, call your Coze agent API, and download the generated analysis report.

Usage:

1. Install dependencies:

```powershell
pip install -r requirements.txt
```

2. Ensure `z_扣子api.py` contains your API URL and Authorization token, or set env vars:

```
setx COZE_API_URL "https://your.coze.site/stream_run"
setx COZE_API_TOKEN "your_token"
```

3. Run the tool:

```powershell
python tools\report_tool.py
```

4. Open http://localhost:7860 in your browser, upload exam images and an optional template, write the prompt, and click Generate.

Notes:
- This tool attempts to extract `url` and Authorization token from `z_扣子api.py` without executing it. If the file uses different shapes, prefer environment variables.
- The script sends images and template encoded as base64 in the payload. Adjust `build_payload` in `tools/report_tool.py` if your agent expects files uploaded differently.
