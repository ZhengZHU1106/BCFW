"""
数据库连接和初始化
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from contextlib import contextmanager
from typing import Generator

from .models import Base
from ..config import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """初始化数据库连接"""
        try:
            # 创建数据库引擎
            self.engine = create_engine(
                DATABASE_CONFIG['url'],
                echo=DATABASE_CONFIG['echo'],
                pool_pre_ping=True  # 连接池预检
            )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            
            logger.info(f"✅ 数据库初始化成功: {DATABASE_CONFIG['url']}")
            
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """数据库会话上下文管理器"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ 数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.session_scope() as session:
                session.execute("SELECT 1")
            logger.info("✅ 数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"❌ 数据库连接测试失败: {e}")
            return False
    
    def reset_database(self):
        """重置数据库（删除所有表并重新创建）"""
        try:
            logger.warning("⚠️  正在重置数据库...")
            Base.metadata.drop_all(bind=self.engine)
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ 数据库重置完成")
        except Exception as e:
            logger.error(f"❌ 数据库重置失败: {e}")
            raise

# 全局数据库管理器实例
db_manager = None

def get_db_manager() -> DatabaseManager:
    """获取数据库管理器单例"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def init_database():
    """初始化数据库"""
    global db_manager
    db_manager = DatabaseManager()
    return db_manager

def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（用于FastAPI依赖注入）"""
    db_manager = get_db_manager()
    with db_manager.session_scope() as session:
        yield session