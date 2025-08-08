import smtplib
from email.mime.text import MIMEText
import logging

def send_email(subject, body, config, recipients):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config['from']
    msg['To'] = ', '.join(recipients)
    
    try:
        with smtplib.SMTP_SSL(config['smtp'], config['port']) as server:
            # server.set_debuglevel(1)  # 输出详细的SMTP通信日志
            server.login(config['from'], config['password'])
            server.sendmail(config['from'], recipients, msg.as_string())
            logging.info("✅ 邮件发送成功！")
            return True
    except Exception as e:
        if str(e) == "(-1, b'\\x00\\x00\\x00')":
            logging.warning("⚠️ 捕获到异常 (-1, b'\\x00\\x00\\x00')，但认为邮件发送成功")
            return True
        logging.error(f"❌ 邮件发送失败: {e}")
        return False