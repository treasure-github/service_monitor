## 📁 项目结构
# service_monitor/
# ├── app.py                ← Flask 主入口
# ├── models.py             ← SQLAlchemy 数据模型
# ├── scheduler.py          ← 检查调度逻辑
# ├── check_service.py      ← HTTP/TCP 检查功能
# ├── mailer.py             ← 邮件发送功能
# ├── templates/
# │   ├── index.html            ← 控制面板
# │   ├── notify.html           ← 邮箱配置页
# │   └── alerts.html           ← 告警历史页
# │   └── edit_service.html     ← 修改服务信息页