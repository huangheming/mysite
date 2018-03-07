from django.core.mail import send_mail, EmailMultiAlternatives
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'

if __name__ == '__main__':
    # send_mail(
    #     '测试邮件',
    #     '邮件内容',
    #     'h397638537@sina.com',
    #     ['397638537@qq.com'],
    # )

    subject, from_email, to = '测试邮件', 'h397638537@sina.com', '397638537@qq.com'
    # text_content是用于当HTML内容无效时的替代txt文本
    text_content = '百度一下，你就知道！'
    html_content = '<p><a href="https://www.baidu.com" target=blank>百度一下，你就知道！</a></p>'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
