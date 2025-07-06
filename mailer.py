import smtplib
from email.mime.text import MIMEText

def send_email(subject, body, config, recipients):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config['from']
    msg['To'] = ', '.join(recipients)
    
    try:
        with smtplib.SMTP_SSL(config['smtp'], config['port']) as server:
            server.login(config['from'], config['password'])
            server.sendmail(config['from'], recipients, msg.as_string())
        print("邮件发送成功！")
    except smtplib.SMTPResponseException as e:
        if e.smtp_code == 250:
            print("邮件发送成功（服务器返回非标准响应）")
        else:
            print(f"SMTP 错误: {e}")
    except Exception as e:
        print(f"发送失败: {e}")