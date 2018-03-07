from django.shortcuts import render, redirect
from login import models
from . import forms
import hashlib
import datetime
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import pytz

# Create your views here.


def hash_code(s, salt='mysite'):
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())
    return h.hexdigest()


def make_confirm_string(user):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.name, now)
    models.ConfirmString.objects.create(code=code, user=user, )
    return code


def send_email(to, code):
    subject = '注册确认邮件'

    text_content = '''感谢注册本系统！
                      如果你看到这条消息，说明你的邮箱服务器不提供HTML链接功能，请联系管理员！'''

    html_content = '''
                        <p>感谢注册本系统！</p>
                        <p>请点击<a href='http://{0}/confirm?code={1}'>链接</a>完成注册确认！</p>
                        <p>此链接有效期为{2}天！</p>
                        '''.format('127.0.0.1:8000', code, settings.CONFIRM_DAYS)

    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def index(request):
    pass
    return render(request, "login/index.html")


def login(request):
    if request.session.get('is_login', None):
        return redirect("/index/")
    if request.method == "POST":
        login_form = forms.UserForm(request.POST)
        print(request.POST)
        print(login_form)
        message = "请检查填写的内容！"
        if login_form.is_valid():
            username = login_form.cleaned_data["name"]
            password = login_form.cleaned_data["password"]
            try:
                user = models.User.objects.get(name=username)
                if not user.has_confirmed:
                    message = "该用户还未通过邮件确认！"
                    return render(request, 'login/login.html', locals())
                if user.password == hash_code(password):
                    request.session['is_login'] = True
                    request.session['user_id'] = user.id
                    request.session['user_name'] = user.name
                    return redirect("/index/")
                else:
                    message = "密码不正确！"
            except:
                message = "用户不存在！"
    else:
        login_form = forms.UserForm()
    return render(request, "login/login.html", locals())


def register(request):
    if request.session.get('is_login', None):
        return redirect('/index/')
    if request.method == 'POST':
        register_form = forms.RegisterForm(request.POST)
        message = '请检查填写的内容！'
        # 验证未通过
        if not register_form.is_valid():
            return render(request, "login/register.html", locals())
        name = register_form.cleaned_data['name']
        password1 = register_form.cleaned_data['password1']
        password2 = register_form.cleaned_data['password2']
        email = register_form.cleaned_data['email']
        sex = register_form.cleaned_data['sex']
        # 校验密码一致性
        if password1 != password2:
            message = '两次输入的密码不相同！'
            return render(request, "login/register.html", locals())
        same_name_user = models.User.objects.filter(name=name)
        # 校验用户名、邮箱
        if same_name_user:
            message = '用户已存在！'
            return render(request, "login/register.html", locals())
        same_email_user = models.User.objects.filter(email=email)
        if same_email_user:
            message = '此邮箱已注册账号！'
            return render(request, "login/register.html", locals())
        new_user = models.User.objects.create()
        new_user.name = name
        new_user.password = hash_code(password1)
        new_user.sex = sex
        new_user.email = email
        new_user.save()

        code = make_confirm_string(new_user)
        send_email(email, code)

        message = '请前往注册邮箱，进行邮件确认！'
        return render(request, 'login/confirm.html', locals())
    register_form = forms.RegisterForm()
    return render(request, "login/register.html", locals())


def logout(request):
    if request.session.get('is_login', None):
        request.session.flush()
    return redirect("/index/")


def confirm(request):
    code = request.GET.get('code', None)
    message = ''
    is_confirmed = False
    try:
        confirm_string = models.ConfirmString.objects.get(code=code)
    except:
        message = '无效的确认请求！'
        return render(request, 'login/confirm.html', locals())
    c_time = confirm_string.c_time
    # now为不含时区的类型（offset-naive），c_time为含时区的类型（offset-aware），需要统一才能比较
    now = datetime.datetime.now().replace(tzinfo=pytz.timezone('UTC'))
    if now > c_time + datetime.timedelta(int(settings.CONFIRM_DAYS)):
        message = '注册码已过期，请重新注册！'
        return render(request, 'login/confirm.html', locals())
    else:
        confirm_string.user.has_confirmed = True
        confirm_string.user.save()
        confirm_string.delete()
        message = '注册成功！'
        is_confirmed = True
    return render(request, 'login/confirm.html', locals())
