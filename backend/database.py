"""
数据库连接和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from config import settings
from models.models import Base

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False, "timeout": 30} if "sqlite" in settings.database_url else {},
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库（创建所有表）"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（用于FastAPI依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """获取数据库会话（用于上下文管理器）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


