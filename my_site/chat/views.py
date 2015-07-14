from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from chat.models import *
import json


class HomeView(TemplateView):
    template_name = "chat/index.html"


def init(request):
    json_response = []
    for conf in request.user.conference_set.all():
        json_response.append(
            {
                'pk': conf.pk,
                'users': conf.get_members_name(),
                'messages_count': conf.get_messages_count(),
            }
        )
    return JsonResponse(json_response)


def messages(request):
    conference_pk = request.POST.get('conference_pk', None)
    message_time_stamp = request.POST.get('message_time_stamp', None)

    conference = Conference.objects.get(pk=conference_pk)
    _messages = conference.get_messages_younger_then(message_time_stamp)
    json_response = {
        'conference_pk': conference_pk,
        'messages': [{'sender': m.sender.username, 'time_stamp': m.time_stamp, 'message': m.message} for m in _messages]
    }
    return JsonResponse(json_response)


def messages_count(request):
    list_conference_pk = json.loads(request.POST.get('list_conference_pk', None))
    json_response = {'old_conferences': [], 'new_conferences': []}
    for conf in request.user.conference_set.all():
        if conf.pk in list_conference_pk:
            json_response['old_conferences'].append(
                {
                    'pk': conf.pk,
                    'messages_count': conf.get_messages_count(),
                }
            )
        else:
            json_response['new_conferences'].append(
                {
                    'pk': conf.pk,
                    'users': conf.get_members_name(),
                    'messages_count': conf.get_messages_count(),
                }
            )
    return JsonResponse(json_response)


def users(request):
    conference_pk = request.POST.get('conference_pk', None)
    conference = Conference.objects.get(pk=conference_pk)
    json_response = conference.get_members_name_with_status()
    return JsonResponse(json_response)


def create_conference(request):
    _users = json.loads(request.POST.get('users', None))
    message = request.POST.get('message', None)
    conference = Conference()
    conference.save()
    for username in _users:
        conference.users.add(User.objects.get(username=username))
    if message is not None:
        conference.add_message(request.user, message)
    return JsonResponse({
        'conference_pk': conference.pk,
        'users': _users
    })


def send(request):
    conference_pk = request.POST.get('conference_pk', None)
    message = request.POST.get('message', None)
    conference = Conference.objects.get(pk=conference_pk)
    conference.add_message(request.user, message)
    return HttpResponse('')


def leave(request):
    conference_pk = request.POST.get('conference_pk', None)
    conference = Conference.objects.get(pk=conference_pk)
    conference.leave(request.user)
    return HttpResponse('')