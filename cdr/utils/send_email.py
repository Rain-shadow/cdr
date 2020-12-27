#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2020-12-27, 0027 17:25
# @Author: 佚名
# @File  : send_email.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from ..config import LOG_DIR_PATH

sender = 'from@rush.b'
receivers = ['3078428762@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

# 创建一个带附件的实例
message = MIMEMultipart()
message['From'] = Header("User", 'utf-8')
message['To'] = Header("Admin", 'utf-8')
subject = '错误信息'
message['Subject'] = Header(subject, 'utf-8')

# 邮件正文内容
message.attach(MIMEText('Noting......', 'plain', 'utf-8'))

# 构造附件1，传送当前目录下的 test.txt 文件
att1 = MIMEText(open(f"{LOG_DIR_PATH}error-last.txt", 'rb').read(), 'base64', 'utf-8')
att1["Content-Type"] = 'application/octet-stream'
# 这里的filename可以任意写，写什么名字，邮件中显示什么名字
att1["Content-Disposition"] = 'attachment; filename="error.txt"'
message.attach(att1)

try:
    smtp_obj = smtplib.SMTP('localhost')
    smtp_obj.sendmail(sender, receivers, message.as_string())
    print("邮件发送成功")
except smtplib.SMTPException:
    print("Error: 无法发送邮件")
