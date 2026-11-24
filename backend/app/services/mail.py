import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from app.config import settings

class MailUnavailable(Exception):
    pass

def send_code(email: str, code: str):
    if settings.mail_mode == 'disabled':
        raise MailUnavailable('邮件服务尚未配置，登录暂不可用')
    if settings.mail_mode == 'file':
        path = Path(settings.dev_mailbox_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'email': email, 'code': code, 'development_only': True}) + '\n')
        return
    message = EmailMessage()
    message['Subject'] = 'Atoms Demo 邮箱验证码'
    message['From'] = settings.mail_from
    message['To'] = email
    message.set_content(f'你的验证码为 {code}，10 分钟内有效。若非本人操作请忽略。')
    try:
        client = smtplib.SMTP_SSL if settings.smtp_security == 'ssl' else smtplib.SMTP
        with client(settings.smtp_host, settings.smtp_port, timeout=12) as smtp:
            if settings.smtp_security == 'starttls':
                smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise MailUnavailable('验证码发送失败，请稍后重试') from exc
