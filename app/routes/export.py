# app/routes/export.py
"""
导出功能蓝图
支持 Excel、CSV、PDF 等格式的报表导出
需要登录保护，部分路由仅管理员可用
"""

from flask import Blueprint, Response, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime
import io
import csv
from typing import Dict, Any

# 假设未来会引入 openpyxl 或 pandas 用于 Excel 复杂导出
# 这里先实现简单 CSV + Excel 基础版（可后续升级 openpyxl）
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    current_app.logger.warning("pandas 未安装，Excel 导出功能受限，仅支持 CSV")

from app.models import User, Project  # 假设已有 Project 模型
from app import db

export_bp = Blueprint('export', __name__, url_prefix='/export')


@export_bp.before_request
@login_required
def require_login():
    """所有导出路由都需要登录"""
    pass


def generate_csv(data: list[Dict[str, Any]], filename: str) -> Response:
    """生成 CSV 响应"""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys() if data else [])
    writer.writeheader()
    writer.writerows(data)

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/csv; charset=utf-8-sig'  # 支持中文 Excel
        }
    )


@export_bp.route('/users.csv', methods=['GET'])
@login_required
def export_users_csv():
    """导出用户列表（仅管理员）"""
    if not current_user.is_admin:
        flash('只有管理员可以导出用户数据', 'danger')
        return redirect(url_for('main.dashboard'))

    users = User.query.all()
    if not users:
        flash('暂无用户数据可导出', 'info')
        return redirect(url_for('admin.users_list'))  # 假设有 admin 路由

    data = [
        {
            'ID': u.id,
            '用户名': u.username,
            '昵称': u.nickname or '',
            '邮箱': u.email or '',
            '是否管理员': '是' if u.is_admin else '否',
            '是否启用': '是' if u.is_active else '否',
            '最后登录': u.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if u.last_login_at else '从未登录',
            '创建时间': u.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for u in users
    ]

    filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return generate_csv(data, filename)


@export_bp.route('/projects.csv', methods=['GET'])
@login_required
def export_projects_csv():
    """导出项目列表（所有登录用户可见）"""
    # 假设 Project 模型已有 owner_id、name、status、volume_m3、freight_usd 等字段
    projects = Project.query.filter_by(owner_id=current_user.id).all()  # 先只导出自己的
    # 如果是管理员，可放开全部： Project.query.all()

    if not projects:
        flash('您暂无项目可导出', 'info')
        return redirect(url_for('main.dashboard'))

    data = [
        {
            '项目ID': p.id,
            '项目名称': p.name,
            '状态': p.status or '未知',
            '总体积(m³)': round(p.volume_m3 or 0, 3),
            '总运费(USD)': round(p.freight_usd or 0, 2),
            '创建者': p.owner.username if p.owner else '未知',
            '创建时间': p.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for p in projects
    ]

    filename = f"projects_{current_user.username}_{datetime.now().strftime('%Y%m%d')}.csv"
    return generate_csv(data, filename)


# 未来可扩展：Excel 版本（依赖 openpyxl 或 pandas）
@export_bp.route('/projects.xlsx', methods=['GET'])
@login_required
def export_projects_excel():
    if not HAS_PANDAS:
        flash('服务器未安装 pandas，无法生成 Excel 文件，请使用 CSV 导出', 'warning')
        return redirect(url_for('export.export_projects_csv'))

    # 与上面 CSV 类似逻辑，生成 DataFrame → to_excel
    # ... 省略具体实现（可后续补充）
    flash('Excel 导出功能开发中，暂使用 CSV', 'info')
    return redirect(url_for('export.export_projects_csv'))


@export_bp.route('/calculator-result', methods=['POST'])
@login_required
def export_calculator_result():
    """从计算器页面导出结果（DDP/KD 等）"""
    # 假设前端 POST 过来 JSON 数据
    result_data = request.json or {}
    if not result_data:
        flash('没有可导出的计算结果', 'warning')
        return redirect(request.referrer or url_for('main.dashboard'))

    # 示例：简单转为 CSV
    flat_data = [
        {'项目名称': result_data.get('project_name', ''),
         '柜数': result_data.get('container_count', 1),
         '单柜 DDP': result_data.get('ddp_per_container', 0),
         '总价 USD': result_data.get('total_ddp', 0),
         '导出时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    ]

    filename = f"calculator_result_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return generate_csv(flat_data, filename)


# 错误处理示例
@export_bp.errorhandler(403)
def forbidden(e):
    flash('无权限访问该导出功能', 'danger')
    return redirect(url_for('main.dashboard'))
