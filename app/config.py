"""应用配置，从 .env 和环境变量读取"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # 数据库（同步模式，MVP 阶段使用 psycopg2）
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://zhixue:zhixue_pass@localhost:5432/zhixue",
    )

    # 文件存储路径
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    STATIC_DIR: Path = Path(os.getenv("STATIC_DIR", "./static"))
    QR_CODE_DIR: Path = Path(os.getenv("QR_CODE_DIR", "./static/qrcodes"))

    # 管理员账号（MVP 固定密码登录）
    ADMIN_USER: str = os.getenv("ADMIN_USER", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "zhixue123")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_DAYS: int = int(os.getenv("JWT_EXPIRE_DAYS", "7"))

    # 文件上传限制
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
    MAX_TOTAL_UPLOAD_MB: int = int(os.getenv("MAX_TOTAL_UPLOAD_MB", "50"))

    # 域名（二维码短链接用）
    DOMAIN: str = os.getenv("DOMAIN", "https://your-domain.com")


settings = Settings()

# 确保目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)
settings.QR_CODE_DIR.mkdir(parents=True, exist_ok=True)
