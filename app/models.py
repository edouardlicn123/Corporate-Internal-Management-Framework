# 文件路径：app/models.py
# 更新日期：2026-02-17
# 功能说明：核心数据库模型定义，包括 User（用户实体，支持登录、权限、偏好）和 SystemSetting（系统全局配置键值对表），供 SQLAlchemy 使用

from flask_login import UserMixin
from app import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    """
    用户表 - 系统核心实体
    用于登录认证、权限控制、项目归属、个人偏好存储等。
    继承 UserMixin 以支持 Flask-Login 的 current_user、is_authenticated、is_active 等功能。
    """
    __tablename__ = 'users'

    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="用户ID（主键）")

    # 登录账号（唯一，必填）
    username = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="登录用户名（唯一，必填）"
    )

    # 显示昵称（可选，非唯一）
    nickname = db.Column(
        db.String(64),
        nullable=True,
        comment="显示昵称（仪表盘、项目成员列表等处优先显示，可中英文）"
    )

    # 密码哈希（永不存储明文）
    password_hash = db.Column(
        db.String(256),
        nullable=False,
        comment="密码哈希值（使用 pbkdf2:sha256 高迭代次数生成）"
    )

    # 邮箱（可选，唯一）
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=True,
        index=True,
        comment="用户邮箱（可选，用于密码重置、通知等）"
    )

    # 权限角色
    is_admin = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        comment="是否为系统管理员（拥有后台管理权限）"
    )

    # 账号状态
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        comment="账号是否可用（False 表示被禁用）"
    )

    # 安全防护
    failed_login_attempts = db.Column(
        db.Integer,
        default=0,
        nullable=False,
        comment="连续登录失败次数，达到阈值后临时锁定"
    )
    locked_until = db.Column(
        db.DateTime,
        nullable=True,
        comment="账号临时锁定的截止时间（为空表示未锁定）"
    )

    # 用户个人偏好（存储在用户表，避免额外表）
    theme = db.Column(
        db.String(20),
        nullable=False,
        default='default',
        comment="个人界面主题：default / dopamine / macaron / teal / uniklo"
    )
    notifications_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment="是否开启系统通知（新项目、任务提醒等）"
    )
    preferred_language = db.Column(
        db.String(10),
        nullable=False,
        default='zh',
        comment="首选界面语言：zh / en"
    )

    # 时间戳
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="账号创建时间（UTC）"
    )
    last_login_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="最后一次成功登录时间（UTC）"
    )

    def __repr__(self):
        display_name = self.nickname or self.username
        return f'<User {display_name} (id:{self.id})>'

    # ──────────────────────────────────────────────
    # 密码相关方法（安全强化）
    # ──────────────────────────────────────────────
    def set_password(self, password: str) -> None:
        """设置密码，使用高强度哈希（pbkdf2:sha256 + 600,000 次迭代，2026年推荐）"""
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256:600000'  # 可根据服务器性能调高到 1000000+
        )

    def check_password(self, password: str) -> bool:
        """验证密码是否匹配"""
        return check_password_hash(self.password_hash, password)

    def record_failed_attempt(self) -> None:
        """记录登录失败，达到阈值后锁定账号"""
        self.failed_login_attempts += 1

        LOCK_THRESHOLD = 5      # 失败 5 次锁定
        LOCK_MINUTES = 30       # 锁定 30 分钟

        if self.failed_login_attempts >= LOCK_THRESHOLD:
            self.locked_until = datetime.utcnow() + timedelta(minutes=LOCK_MINUTES)

    def reset_failed_attempts(self) -> None:
        """登录成功或手动重置时，清零失败计数并解除锁定"""
        self.failed_login_attempts = 0
        self.locked_until = None

    def is_locked(self) -> bool:
        """判断账号是否处于锁定状态"""
        return self.locked_until is not None and self.locked_until > datetime.utcnow()

    def record_login(self) -> None:
        """记录成功登录时间（调用后需 commit）"""
        self.last_login_at = datetime.utcnow()


class SystemSetting(db.Model):
    """
    系统设置表 - 键值对存储（每条配置一行）
    整个系统只有多条记录，每条记录代表一个配置项（key + value）
    通过 SettingsService 统一读写，默认值在服务层处理
    """
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True, comment="主键")

    key = db.Column(
        db.String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="配置键名（唯一，例如 'upload_max_size_mb'）"
    )

    value = db.Column(
        db.Text,
        nullable=False,
        comment="配置值（统一存字符串，服务层负责类型转换）"
    )

    description = db.Column(
        db.String(255),
        nullable=True,
        comment="配置项描述"
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="最后更新时间"
    )

    def __repr__(self):
        return f'<SystemSetting {self.key}: {self.value}>'
