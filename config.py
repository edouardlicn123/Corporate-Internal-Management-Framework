# config.py
import os
from pathlib import Path
import secrets
from datetime import timedelta
from typing import Any

# 项目根目录（从 config.py 向上两级，通常是 run.py 所在目录）
BASE_DIR = Path(__file__).resolve().parent

# 调试：打印实际使用的项目根目录（开发时有用，生产可注释）
if os.environ.get('FLASK_ENV', 'development').lower() == 'development':
    print(f"[DEBUG] 项目根目录 (BASE_DIR): {BASE_DIR}")
    print(f"[DEBUG] 数据库预期路径: {BASE_DIR / 'instance' / 'site.db'}")

class BaseConfig:
    """基础配置 - 所有环境共用"""

    # 项目根目录（供其他地方使用）
    BASE_DIR = BASE_DIR

    # =============================================
    # 核心安全 - SECRET_KEY（最高优先级）
    # =============================================
    SECRET_KEY = (
        os.environ.get('SECRET_KEY')
        or os.environ.get('FLASK_SECRET_KEY')
        or secrets.token_urlsafe(48)  # 推荐 64+ 字符
    )

    # 随机密钥警告逻辑
    _using_random_key = not (os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY'))
    if _using_random_key:
        msg = (
            f"[{os.getenv('START_TIME', 'unknown')}] "
            "【严重安全警告】未设置 SECRET_KEY，使用临时随机密钥！\n"
            "  → 生产环境必须通过环境变量提供固定强密钥\n"
            "  生成命令：python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
        if os.environ.get('FLASK_ENV') == 'production':
            raise RuntimeError(msg)
        print(msg)

    # =============================================
    # 数据库 - 强制使用项目根下的 instance/site.db
    # =============================================
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        f"sqlite:///{BASE_DIR / 'instance' / 'site.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
    }

    # 开发时可选开启 SQL 日志（取消注释即可）
    # if os.environ.get('FLASK_ENV', 'development').lower() == 'development':
    #     SQLALCHEMY_ECHO = True

    # =============================================
    # 文件上传 - 统一放在项目根下 persistent_uploads
    # =============================================
    UPLOAD_FOLDER = str(BASE_DIR / 'persistent_uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'docx', 'csv'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MiB

    # =============================================
    # 会话 & Cookie 安全
    # =============================================
    SESSION_COOKIE_NAME = 'ffe_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)

    # =============================================
    # 分页 & 业务通用
    # =============================================
    ITEMS_PER_PAGE = 20
    DEFAULT_PAGE_SIZE = 20
    MAX_PROJECT_NAME_LENGTH = 120
    MAX_USERNAME_LENGTH = 64

    # =============================================
    # 其他 Flask 推荐配置
    # =============================================
    JSON_SORT_KEYS = False
    JSON_AS_ASCII = False
    PROPAGATE_EXCEPTIONS = True


class DevelopmentConfig(BaseConfig):
    ENV = 'development'
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    PREFERRED_URL_SCHEME = 'http'


class TestingConfig(BaseConfig):
    ENV = 'testing'
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    ENV = 'production'
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 86400

    if BaseConfig._using_random_key:
        raise RuntimeError(
            "生产环境必须通过环境变量 SECRET_KEY 设置强密钥！\n"
            "禁止使用随机生成的临时密钥。"
        )


# 配置映射
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}


def get_config() -> type[BaseConfig]:
    """根据环境变量返回配置类"""
    env = os.environ.get('FLASK_ENV', 'development').lower()
    return config.get(env, config['default'])
