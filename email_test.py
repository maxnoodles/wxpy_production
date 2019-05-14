# coding=utf-8
import smtplib
from email.message import EmailMessage


def my_email(content):
    msg_from = '924461845@qq.com'       # 发送方邮箱
    passwd = 'ivgklabsopzqbfid'     # 填入发送方邮箱的授权码
    msg_to = '924461845@qq.com'     # 收件人邮箱

    subject = "python邮件报警"     # 主题
    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to

    with smtplib.SMTP_SSL("smtp.qq.com", 465) as s:
        s.login(msg_from, passwd)
        s.send_message(msg)
        print("发送成功")


if __name__ == '__main__':
    content = "这是我使用python smtplib及email模块发送的邮件"     # 内容
    my_email(content)