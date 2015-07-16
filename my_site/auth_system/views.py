from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.template import RequestContext
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
import json


@csrf_protect
def log_out(request):
    """
    Выход с сайта
    """
    logout(request)
    return HttpResponse('')


@csrf_protect
def log_in(request):
    """
    Вход на сайт
    return:{
        is_error: true false
        message: сообщение
    }
    """
    obj = {}
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                obj['is_error'] = False
                obj['message'] = "Вход успешно выполнен."
                return JsonResponse(obj)
            else:
                obj['is_error'] = True
                obj['message'] = 'Ваша учетная запись не активна. За подробностями обращайтесь к администрации сайта.'
        else:
            obj['is_error'] = True
            obj['message'] = 'Неправильный логин или пароль.'
    return JsonResponse(obj)


@csrf_protect
def register(request):
    """
    Регистрация пользователя
    return:{
        is_error: true false
        message: сообщение
    }
    """
    obj = {}
    if request.method == 'POST':
        new_user_form = UserCreationForm(request.POST)
        if new_user_form.is_valid():
            new_user_form.save()
            obj['is_error'] = False
            obj['message'] = "Вы успешно зарегистрированы."
        else:
            obj['is_error'] = True
            obj['message'] = "Либо пароли не совпадают, либо пользователь с таким именем уже существует."
    return JsonResponse(obj)


# todo добавить регистрацию пользователей
# todo добавить возможность редактировать личные данные пользователей