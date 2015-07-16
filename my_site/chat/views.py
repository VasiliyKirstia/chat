from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from chat.models import *
import json

from django.views.decorators.csrf import csrf_exempt, csrf_protect
# todo проблема с добавлением конференции в которой нет создающего
# todo проблема удалением конференций, общая проблема безопастности

class HomeView(TemplateView):
    template_name = "chat/index.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['users_list'] = User.objects.all()
        return context


@csrf_protect
def init(request):
    json_response = []
    for conf in request.user.conference_set.all():
        json_response.append(
            {
                'pk': conf.pk,
                'users': conf.get_members_name(),
                'messages_count': conf.get_new_messages_count(request.user),
            }
        )
    return JsonResponse(json_response, safe=False)


@csrf_protect
def messages(request):
    conference_pk = request.POST.get('conference_pk', None)
    message_time_stamp = request.POST.get('message_time_stamp', None)

    conference = Conference.objects.get(pk=conference_pk)
    if message_time_stamp != 0:
        link = ConferenceUserLink.objects.get(user=request.user, conference=conference)
        link.last_message_date = message_time_stamp
        link.save()
        _messages = conference.get_messages_younger_then(message_time_stamp)
    else:
        _messages = conference.get_messages()

    json_response = [{'sender': m.sender.username, 'time_stamp': m.time_stamp, 'message': m.message} for m in _messages]
    return JsonResponse(json_response, safe=False)


@csrf_protect
def messages_count(request):
    list_conference_pk = json.loads(request.POST.get('list_conference_pk', None))
    json_response = {'old_conferences': [], 'new_conferences': []}
    for conf in request.user.conference_set.all():
        if conf.pk in list_conference_pk:
            json_response['old_conferences'].append(
                {
                    'pk': conf.pk,
                    'messages_count': conf.get_new_messages_count(request.user),
                }
            )
        else:
            json_response['new_conferences'].append(
                {
                    'pk': conf.pk,
                    'users': conf.get_members_name(),
                    'messages_count': conf.get_new_messages_count(request.user),
                }
            )
    return JsonResponse(json_response, safe=False)


@csrf_protect
def users(request):
    conference_pk = request.POST.get('conference_pk', None)
    conference = Conference.objects.get(pk=conference_pk)
    json_response = conference.get_members_name_with_status()
    return JsonResponse(json_response, safe=False)


@csrf_protect
def create_conference(request):
    _users = json.loads(request.POST.get('users', None))
    message = request.POST.get('message', None)
    _conference = Conference()
    _conference.save()
    for username in _users:
        link = ConferenceUserLink(conference=_conference,
                                  user=User.objects.get(username=username),
                                  last_message_date=timezone.now().timestamp())
        link.save()
    if message is not None and len(message) > 0:
        _conference.add_message(request.user, message)
    return JsonResponse({
        'conference_pk': _conference.pk,
        'users': _users
    }, safe=False)


@csrf_protect
def send(request):
    conference_pk = request.POST.get('conference_pk', None)
    message = request.POST.get('message', None)
    conference = Conference.objects.get(pk=conference_pk)
    conference.add_message(request.user, message)
    return HttpResponse('')


@csrf_protect
def leave(request):
    conference_pk = request.POST.get('conference_pk', None)
    conference = Conference.objects.get(pk=conference_pk)
    conference.leave(request.user)
    return HttpResponse('')