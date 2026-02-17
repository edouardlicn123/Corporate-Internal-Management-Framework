# FFE 项目跟进系统 - 开发高危注意事项 & 核心规范（必读）

**最后重大更新日期**：2026年2月16日  
**重要程度**：★★★★★  
**阅读对象**：所有参与本项目的开发者、AI 助手、代码审查者  
**阅读要求**：**每次开发、审代码、向 AI 提问前必须完整阅读本文件一遍**，尤其是涉及模板、路由、服务层、新增文件时。

## 一、最高优先级铁律（违反即中断合作 / 打回重写）

1. **AI 必须全程使用中文与开发者沟通**  
   - 不管用户贴的代码、报错信息、英文文档、英文报错栈，**AI 回答一律用中文**  
   - 禁止出现“当然”“Sure”“Here you go”等英文开头  
   - 代码注释、说明文字也优先使用中文（英文仅限必要的技术术语）

2. **所有新增/修改的文件，必须在文件最顶部添加标准注释块**  
   必须包含以下三部分（顺序固定，每行独立）：

   - 文件路径：完整相对路径（从项目根目录开始）
   - 更新日期：格式 YYYY-MM-DD（建议使用当天日期）
   - 功能说明：一句话或两句简洁描述该文件的主要作用、核心功能或设计意图（中文）

   正确示例（Python 文件）：
   ```python
   # 文件路径：app/routes/calculator.py
   # 更新日期：2026-02-17
   # 功能说明：计算器模块路由集合，负责接收前端请求、参数校验并调用服务层进行体积/运费计算
   ```

   正确示例（模板文件）：
   ```html
   {# 文件路径：app/templates/calculator/kdsize_calculator.html #}
   {# 更新日期：2026-02-17 #}
   {# 功能说明：KD 包装体积计算器主页面，提供品类选择、尺寸输入、计算结果展示及记录管理 #}
   ```

   正确示例（CSS 文件）：
   ```css
   /* 文件路径：app/static/css/base.css */
   /* 更新日期：2026-02-17 */
   /* 功能说明：全局基础样式、重置样式、通用布局类和响应式断点定义 */
   ```

   **AI 输出任何完整文件内容时，必须严格遵守此三行注释格式，否则视为无效输出。**

3. **前端模板 class 名与结构必须严格参考 docs/9css-elements-reference.md**  
   - 禁止随意发明新的 class 名称  
   - 所有卡片、按钮、标题、布局容器、颜色类、间距类等，**优先 100% 复用已有定义**  
   - 常用强制复用元素示例（不完整，详见参考文档）：
     - 欢迎/主标题：`.welcome-title`
     - 设置/表单标题：`.settings-title`
     - 仪表盘卡片组容器：`.dashboard-cards`
     - 单卡片：`.card-entry`
     - 通用按钮：`.card-btn` + `.primary-btn` / `.success-btn` / `.info-btn` / `.warning-btn` 等
     - 主题色跟随变量：`--primary`, `--success`, `--info`, `--warning`, `--danger`
   - 新增页面/组件前，必须先打开 `9css-elements-reference.md` 核对

4. **前后端分离设计原则（路由 + 服务层）——必须严格遵守**  
   当前及未来所有业务逻辑必须遵循以下分层：

   ```
   路由层（routes/*.py）          → 只负责接收请求、参数校验、调用 service、返回响应
   服务层（services/*.py）         → 核心业务逻辑、计算、数据库操作、复杂处理
   模型层（models.py）             → 数据定义与简单关系查询
   工具层（utils/*.py）            → 通用辅助函数（权限、格式化、加密等）
   ```

   **严禁** 在路由函数里直接写数据库查询、复杂计算、文件处理等逻辑。

   推荐写法示例：
   ```python
   # 文件路径：app/routes/calculator.py
   # 更新日期：2026-02-17
   # 功能说明：计算器模块路由集合，负责接收前端请求、参数校验并调用服务层进行体积/运费计算

   @calculator_bp.route('/kdsize', methods=['POST'])
   def calculate_kd_volume():
       data = request.form
       result = kd_volume_service.calculate(data)   # 服务层处理
       return jsonify(result)
   ```

5. **任何开发/修改前，必须先阅读 docs/1Development_Progress.md**  
   - 该文件记录了当前系统已完成的功能、已修复的坑、当前架构状态  
   - 避免重复造轮子、覆盖已有功能、引入已知问题  
   - 阅读顺序建议：  
     1. 1Development_Progress.md（当前状态）  
     2. 本 README（规范与雷区）  
     3. 9css-elements-reference.md（前端样式规范）  
     4. 具体模块策划书（如 module_kdsize_calculator.md）

6. **AI 输出代码时的优先级规则**  
   - **优先输出完整文件**（包含顶部三行注释、全部 import、全部代码）  
   - **只有在文件非常长（>600行）时，才允许只输出 diff 片段**  
   - 片段输出时必须明确说明：
     - 文件完整路径
     - 是新增文件 / 替换全部 / 只修改某部分
     - 建议的上下文行号（如果可提供）

## 二、其他重要开发雷区（快速自查清单）

- Jinja2 注释必须用 `{# ... #}`，**绝不能用 <!-- ... -->**
- 所有路由必须显式声明 `methods=['GET']` 或 `methods=['GET', 'POST']`
- 新建蓝图时，**强烈建议** 加上 `@bp.before_request @login_required` 全蓝图登录保护
- 用户输入（尤其是 username、nickname）必须 `.strip()`
- 生产环境 SECRET_KEY 长度必须 ≥48 字符
- 日志使用 `app.logger`，不要直接 print()
- 数据库初始化使用 `db.create_all()` 或迁移脚本，**不要** 混用

## 三、一句话终极执行顺序（每次动手前默念）

1. 打开 `docs/1Development_Progress.md` → 确认当前进度与已完成模块  
2. 打开本 README → 检查是否踩雷  
3. 打开 `docs/9css-elements-reference.md` → 确定要用的 class 名  
4. 规划路由 + service 分层  
5. 写代码（顶部必须加三行标准注释）  
6. 输出完整文件给开发者审核


