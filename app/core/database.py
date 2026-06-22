"""异步数据库引擎和会话（备用 - 当前使用同步模式）

Windows + Python 3.13 下 asyncpg 存在已知兼容性问题，
MVP 阶段使用同步 SQLAlchemy + psycopg2，后续可切回异步。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_size=10, max_overflow=20, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
