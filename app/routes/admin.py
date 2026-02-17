# 文件路径：app/routes/admin.py
# 更新日期：2026-02-17
# 功能说明：后台管理模块路由集合，负责接收请求、表单校验、调用用户/设置服务层、渲染模板或返回响应，不包含任何数据库操作或核心业务逻辑

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.forms.admin_forms import UserSearchForm, UserForm, SystemSettingsForm
from app.services.user_service import UserService
from app.services.settings_service import SettingsService
from werkzeug.exceptions import Forbidden

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def require_admin():
    """所有后台路由要求登录且必须是管理员"""
    if not current_user.is_admin:
        flash('需要管理员权限访问该页面', 'danger')
        return redirect(url_for('main.dashboard'))


@admin_bp.route('/dashboard', methods=['GET'])
def admin_dashboard():
    """后台仪表盘 - 显示用户统计等概览"""
    try:
        stats = UserService.get_user_stats()
        return render_template('admin/dashboard.html', stats=stats)
    except Exception as e:
        current_app.logger.error(f"仪表盘加载失败: {str(e)}", exc_info=True)
        flash('加载统计数据失败，请稍后重试', 'danger')
        return render_template('admin/dashboard.html', stats={})


@admin_bp.route('/system-users', methods=['GET'])
def system_users():
    """系统用户列表页面 - 支持搜索和活跃过滤"""
    form = UserSearchForm(request.args)

    search_term = form.username.data if form.username.data else None
    only_active = form.is_active.data if form.is_active.data is not None else True

    try:
        users = UserService.get_user_list(
            search_term=search_term,
            only_active=only_active
        )
        return render_template('admin/system_users.html', users=users, form=form)
    except Exception as e:
        current_app.logger.error(f"加载用户列表失败: {str(e)}", exc_info=True)
        flash(f'加载用户列表失败：{str(e)}', 'danger')
        return render_template('admin/system_users.html', users=[], form=form)


@admin_bp.route('/system-user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_bp.route('/system-user/create', methods=['GET', 'POST'], defaults={'user_id': None})
def user_edit(user_id=None):
    """用户编辑 / 新建页面"""
    is_edit = user_id is not None

    user = None
    if is_edit:
        user = UserService.get_user_by_id(user_id)
        if not user:
            flash('用户不存在或无权限访问', 'danger')
            return redirect(url_for('admin.system_users'))

    form = UserForm(
        obj=user,
        is_edit=is_edit,
        original_username=user.username if user else None,
        original_email=user.email if user else None
    )

    if form.validate_on_submit():
        try:
            if is_edit:
                UserService.update_user(
                    user_id=user_id,
                    username=form.username.data,
                    nickname=form.nickname.data,
                    email=form.email.data,
                    password=form.password.data if form.password.data else None,
                    is_admin=form.is_admin.data,
                    is_active=form.is_active.data
                )
                flash('用户信息更新成功', 'success')
            else:
                UserService.create_user(
                    username=form.username.data,
                    nickname=form.nickname.data,
                    email=form.email.data,
                    password=form.password.data,
                    is_admin=form.is_admin.data
                )
                flash('新用户创建成功', 'success')

            return redirect(url_for('admin.system_users'))

        except ValueError as ve:
            flash(str(ve), 'danger')
        except PermissionError:
            flash('系统管理员账号禁止编辑', 'danger')
        except Exception as e:
            current_app.logger.error(f"用户保存失败: {str(e)}", exc_info=True)
            flash('保存失败，请检查输入或联系管理员', 'danger')

    return render_template(
        'admin/system_user_edit.html',
        form=form,
        user=user,
        is_edit=is_edit
    )


@admin_bp.route('/system-user/toggle-active/<int:user_id>', methods=['POST'])
def toggle_active(user_id):
    """AJAX 或表单切换用户启用/禁用状态"""
    active = request.form.get('active') == 'true'

    try:
        UserService.toggle_user_active(user_id, active)
        status_text = "启用" if active else "禁用"
        flash(f'用户已{status_text}', 'success')
    except ValueError as ve:
        flash(str(ve), 'danger')
    except PermissionError:
        flash('系统管理员账号禁止更改状态', 'danger')
    except Exception as e:
        current_app.logger.error(f"用户状态切换失败: {str(e)}", exc_info=True)
        flash('操作失败，请稍后重试', 'danger')

    return redirect(url_for('admin.system_users'))


@admin_bp.route('/system-settings', methods=['GET', 'POST'])
def system_settings():
    """系统设置页面 - 查看/保存全局配置"""
    # 获取当前设置用于预填充表单
    try:
        current_settings = SettingsService.get_all_settings()
    except Exception as e:
        current_app.logger.error(f"加载系统设置失败: {str(e)}", exc_info=True)
        flash('加载设置失败，请检查数据库或联系管理员', 'danger')
        current_settings = {}

    # 创建表单并预填充
    form = SystemSettingsForm(data=current_settings)

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                updated_count = SettingsService.save_settings_bulk(form.data)
                flash(f'设置保存成功（共更新 {updated_count} 项）', 'success')
                return redirect(url_for('admin.system_settings'))
            except Exception as e:
                current_app.logger.error(f"设置保存失败: {str(e)}", exc_info=True)
                flash('保存失败，请检查输入格式或联系管理员', 'danger')
        else:
            flash('表单验证失败，请检查输入内容', 'danger')

    # 无论成功或失败，都传递 form 和 settings
    return render_template(
        'admin/system_settings.html',
        form=form,
        settings=current_settings
    )


@admin_bp.errorhandler(403)
@admin_bp.errorhandler(Forbidden)
def forbidden_error(e):
    flash('权限不足，无法访问该页面', 'danger')
    return redirect(url_for('main.dashboard'))
