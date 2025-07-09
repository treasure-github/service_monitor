from apscheduler.schedulers.background import BackgroundScheduler
from models import db, Service, NotifyConfig, AlertLog
from check_service import check_service
from mailer import send_email
from datetime import datetime
from datetime import timedelta
from threading import Lock
import logging
import os
from util import get_bj_now


_lock = Lock()
_app = None  # 全局记录 app
alert_interval_minutes = 10  # 间隔 N 分钟发送邮件告警
scheduler = BackgroundScheduler()

def get_notify_config():
    cfg = NotifyConfig.query.first()
    return {
        'smtp': cfg.smtp,
        'port': cfg.port,
        'from': cfg.email_from,
        'to': cfg.email_to,
        'password': cfg.password
    } if cfg else None

def job_check_all_services():
    # logging.info("当前任务列表：", scheduler.get_jobs())
    if not _lock.acquire(blocking=False):
        logging.info("🔒 上一个任务还未完成，跳过本次执行")
        return

    try:
        with _app.app_context():
            services = Service.query.all()
            notify_config = get_notify_config()

            if not notify_config:
                logging.info("❌ 未配置通知邮箱（NotifyConfig），跳过发送告警邮件。")
                return

            for s in services:
                if not s.enabled:
                    continue  # 跳过未启用的服务
                
                ok, msg = check_service(s)
                logging.info(f"---->{ok},{msg}")

                send_to_email = s.alert_emails.split(',') if s.alert_emails else []
                if not send_to_email and notify_config.get('to'):
                    send_to_email = notify_config['to'].split(',')

                if ok:
                    if s.alerted:
                        if send_to_email:
                            send_email(
                                f"\u2705 恢复: {s.name}",
                                f"{s.target} 已恢复",
                                notify_config,
                                recipients=send_to_email
                            )
                        db.session.add(AlertLog(service_id=s.id, status='recovery', message=f"{s.target} 恢复", recipients=','.join(send_to_email)))
                        s.alerted = False
                    s.fail_count = 0
                    s.last_alert_time = None
                else:
                    s.fail_count += 1
                    now = get_bj_now().replace(tzinfo=None)
                    should_alert = False

                    if s.fail_count >= s.max_failures:
                        if not s.alerted:
                            should_alert = True
                        elif s.last_alert_time is None or (now - s.last_alert_time) > timedelta(minutes=alert_interval_minutes):
                            should_alert = True

                    if should_alert and send_to_email:
                            send_email(
                                f"❌ 异常: {s.name}",
                                f"{s.target} 连续失败 {s.fail_count} 次: {msg}",
                                notify_config,
                                recipients=send_to_email
                            )
                            s.alerted = True
                            s.last_alert_time = now
                            db.session.add(AlertLog(service_id=s.id, status='alert', message=f"{s.target} 异常: {msg}",recipients=','.join(send_to_email)))
            
            db.session.commit()

    finally:
        _lock.release()
                    
def start(app):
    global _app
    _app = app

    # 只在子进程启动调度器
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        print("调试模式父进程，跳过启动调度器")
        return

    scheduler.add_job(
                    job_check_all_services,
                    'interval', 
                    seconds=5,    #1分钟执行一次 minutes  seconds
                    coalesce=True,  #有多个调度堆积（比如挂起或异常后恢复），只执行一次补偿
                    max_instances=1 #限制同一任务同一时间只能有一个实例 
                    ) 
    scheduler.start()

