# 文件路径：app/routes/__init__.py
# 更新日期：2026-02-17
# 功能说明：所有蓝图（Blueprint）的统一注册入口文件，在应用工厂中调用此函数一次性注册所有路由模块，确保路由结构模块化、可维护、易扩展

from flask import Blueprint

# 导入各个功能模块的蓝图（每个蓝图文件需在顶部定义 bp = Blueprint(...) 并导出 bp）

from .auth import auth_bp           # 认证相关路由（登录、登出、忘记密码等）
from .main import main_bp           # 主页面路由（仪表盘、个人中心、偏好设置等）
from .admin import admin_bp         # 后台管理路由（用户管理、系统设置等）

# 计算器模块暂时禁用（文件未完整实现，避免启动报错）
# from .calculator import calculator_bp  # 计算器模块路由（KD体积、海运费用等）

# 尚未实现的模块（保持注释，待开发后再放开）
# from .project import project_bp     # 项目跟进相关路由
# from .export import export_bp       # 数据导出路由（Excel/PDF 等）

# 可选：未来 API 蓝图（版本化）
# from .api.v1 import api_v1_bp


def register_blueprints(app):
    """
    统一注册所有蓝图的入口函数
    在 app/__init__.py 的 create_app() 中调用此函数
    注册顺序：先核心路由 → 认证 → 管理后台 → 业务模块 → API（如果有）
    """
    # 核心路由（无前缀或根路径）
    app.register_blueprint(main_bp)                     # 仪表盘、首页等

    # 认证路由（统一前缀）
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # 管理后台（需管理员权限）
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # 计算器模块暂时禁用（文件未完整实现，避免启动报错）
    # app.register_blueprint(calculator_bp, url_prefix='/calculator')

    # 待开发模块（示例）
    # app.register_blueprint(project_bp, url_prefix='/project')
    # app.register_blueprint(export_bp, url_prefix='/export')

    # 未来可能的 API 蓝图
    # app.register_blueprint(api_v1_bp, url_prefix='/api/v1')

    # 注册完成日志（生产环境可见，便于排查启动问题）
    app.logger.info("所有蓝图注册完成：auth, main, admin 已加载")


# 额外提示：
# - 如果新增蓝图，只需：
#   1. 在 app/routes/ 下新建 xxx.py 并定义 bp
#   2. 在本文件顶部 import xxx_bp
#   3. 在 register_blueprints() 中添加 app.register_blueprint(...)
# - 所有业务蓝图（admin、calculator、project 等）建议在各自文件中添加：
#     @bp.before_request
#     @login_required
#     def require_login():
#         pass
# - 当前 calculator 蓝图已临时禁用，待 calculator.py 文件完整实现（包含 calculator_bp 定义）后再放开注册
