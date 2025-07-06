from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from util import get_bj_now

db = SQLAlchemy()

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    target = db.Column(db.String(200))
    check_type = db.Column(db.String(10))
    keyword = db.Column(db.String(100))
    fail_count = db.Column(db.Integer, default=0)
    max_failures = db.Column(db.Integer, default=3)
    alerted = db.Column(db.Boolean, default=False)
    alert_emails = db.Column(db.String(300))
    last_alert_time = db.Column(db.DateTime)
    enabled = db.Column(db.Boolean, default=True)
    method = db.Column(db.String(10), default='GET')


class NotifyConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    smtp = db.Column(db.String(100))
    port = db.Column(db.Integer)
    email_from = db.Column(db.String(100))
    email_to = db.Column(db.String(100))
    password = db.Column(db.String(100))

class AlertLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    status = db.Column(db.String(10))  # alert/recovery
    message = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=get_bj_now())
    recipients = db.Column(db.String(300))