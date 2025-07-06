from flask import Flask, render_template, request, redirect, url_for, send_file
from models import db, Service, NotifyConfig, AlertLog
from scheduler import start as start_scheduler
from datetime import datetime
import csv
from io import StringIO, BytesIO
from flask import flash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///monitor.db'
app.config['SECRET_KEY'] = 'secret'
db.init_app(app)

@app.route('/')
def index():
    services = Service.query.all()
    return render_template('index.html', services=services)

@app.route('/add', methods=['POST'])
def add_service():
    s = Service(
        name=request.form['name'],
        check_type=request.form['check_type'],
        target=request.form['target'],
        keyword=request.form.get('keyword'),
        alert_emails=request.form.get('alert_emails', ''),
        method=request.form.get('method', ''),
        max_failures=int(request.form.get('max_failures', 3))
    )
    db.session.add(s)
    db.session.commit()
    return redirect('/')

@app.route('/notify', methods=['GET', 'POST'])
def notify():
    cfg = NotifyConfig.query.first() or NotifyConfig()
    if request.method == 'POST':
        cfg.smtp = request.form['smtp']
        cfg.port = int(request.form['port'])
        cfg.email_from = request.form['email_from']
        cfg.email_to = request.form['email_to']
        cfg.password = request.form['password']
        db.session.add(cfg)
        db.session.commit()
    return render_template('notify.html', cfg=cfg)

@app.route('/alerts/<int:service_id>')
def view_alerts(service_id):
    service = Service.query.get_or_404(service_id)
    page = request.args.get('page', 1, type=int)
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    query = AlertLog.query.filter_by(service_id=service_id)
    if start_time:
        query = query.filter(AlertLog.timestamp >= datetime.fromisoformat(start_time))
    if end_time:
        query = query.filter(AlertLog.timestamp <= datetime.fromisoformat(end_time))

    logs = query.order_by(AlertLog.timestamp.desc()).paginate(page=page, per_page=10)
    return render_template("alerts.html", service=service, logs=logs.items, pagination=logs,
                           start_time=start_time, end_time=end_time)

@app.route('/alerts/<int:service_id>/export')
def export_alerts(service_id):
    service = Service.query.get_or_404(service_id)
    query = AlertLog.query.filter_by(service_id=service_id)

    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    if start_time:
        query = query.filter(AlertLog.timestamp >= datetime.fromisoformat(start_time))
    if end_time:
        query = query.filter(AlertLog.timestamp <= datetime.fromisoformat(end_time))

    logs = query.order_by(AlertLog.timestamp.desc()).all()

    # 先写入 StringIO（文本）
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['时间', '状态', '详情', '收件人'])
    for log in logs:
        status = '异常' if log.status == 'alert' else '恢复'
        writer.writerow([log.timestamp, status, log.message, log.recipients])

    # 编码为 UTF-8 字节流写入 BytesIO
    mem = BytesIO()
    mem.write(si.getvalue().encode('utf-8-sig'))  # 用 utf-8-sig 避免 Excel 打开乱码
    mem.seek(0)

    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='alerts.csv')

@app.route('/alerts/<int:service_id>/delete', methods=['POST'])
def delete_alerts(service_id):
    service = Service.query.get_or_404(service_id)
    AlertLog.query.filter_by(service_id=service.id).delete()
    db.session.commit()
    flash("已清空告警历史")
    return redirect(url_for('view_alerts', service_id=service.id))


@app.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)

    # 删除关联告警记录
    AlertLog.query.filter_by(service_id=service.id).delete()

    # 删除服务本身
    db.session.delete(service)
    db.session.commit()

    return redirect('/')


@app.route('/edit/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)

    if request.method == 'POST':
        service.name = request.form['name']
        service.check_type = request.form['check_type']
        service.target = request.form['target']
        service.keyword = request.form.get('keyword', '')
        service.alert_emails = request.form.get('alert_emails', '')
        service.method=request.form.get('method', '')
        service.max_failures = int(request.form.get('max_failures', 3))

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_service.html', s=service)

@app.route("/toggle/<int:service_id>", methods=["POST"])
def toggle_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.enabled = not service.enabled
    db.session.commit()
    return redirect(url_for("index")) 


with app.app_context():
    db.create_all()
    start_scheduler(app)


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=5001)   



