"""二维码生成工具"""

import uuid
from pathlib import Path

import qrcode

from app.config import settings


def generate_qrcode(paper_id: uuid.UUID) -> str:
    """为试卷生成二维码图片，返回可公开访问的 URL 路径"""
    content = f"{settings.DOMAIN}/s?p={paper_id}"
    img = qrcode.make(content)

    filename = f"{paper_id}.png"
    filepath = Path(settings.QR_CODE_DIR) / filename
    img.save(str(filepath))

    return f"/static/qrcodes/{filename}"
