# coding=utf-8
import smtplib
from email.message import EmailMessage
from setting import *
from email.utils import make_msgid

msg_from = MSG_from     # 发送方邮箱
msg_pw = MSG_PW     # 填入发送方邮箱的授权码
msg_to = MSG_to     # 收件人邮箱


def error_alarm(content):
    subject = "python邮件报警"     # 主题
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to
    msg.set_content(content)

    with smtplib.SMTP_SSL("smtp.qq.com", 465) as s:
        s.login(msg_from, msg_pw)
        s.send_message(msg)
        print("发送成功")


def send_qr(fp):
    subject = "登录二维码"     # 主题
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to

    msg.set_content('aaa')
    img_cid = make_msgid()
    msg.add_alternative(f'<html><body><img src="cid:{img_cid[1:-1]}" alt="imageid"></body></html>', subtype='html')

    with open(fp, 'rb') as f:
        msg.get_payload()[1].add_related(f.read(), 'image', 'png', cid=img_cid)

    with smtplib.SMTP_SSL("smtp.qq.com", 465) as s:
        s.login(msg_from, msg_pw)
        s.send_message(msg)


if __name__ == '__main__':

    content = "二维码测试"     # 内容
    error_alarm(content)
    send_qr('QR.png')



