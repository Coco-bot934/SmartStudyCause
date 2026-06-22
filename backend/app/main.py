"""FastAPI 应用入口"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1 import auth_router, classes_router, papers_router, submissions_router
from app.config import settings

app = FastAPI(
    title="知学 — 学情分析工具 API",
    description="K12 学情分析工具后端服务",
    version="1.4.0",
)

# ── 静态文件路由 ──────────────────────────────────────────────
# 确保静态目录存在
settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)
settings.QR_CODE_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# ── 注册路由 ──────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(classes_router)
app.include_router(papers_router)
app.include_router(submissions_router)


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok"}
