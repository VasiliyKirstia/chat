from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from chat.models import *
import json

from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

class HomeView(TemplateView):
    template_name = "chat/index.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['users_list'] = User.objects.all().exclude(pk=self.request.user.pk)
        return context



@csrf_protect
@login_required
def init(request):
    json_response = []
    for conf in request.user.conference_set.all():
        json_response.append(
            {
                'pk': conf.pk,
                'users': conf.get_members_names(request.user),
                'messages_count': conf.get_new_messages_count(request.user),
            }
        )
    return JsonResponse(json_response, safe=False)


@csrf_protect
@login_required
def messages(request):
    conference_pk = request.POST.get('conference_pk', None)
    message_time_stamp = request.POST.get('message_time_stamp', None)

    if conference_pk is None:
        raise Http404()

    if message_time_stamp is None:
        raise Http404()

    conference = get_object_or_404(Conference, pk=conference_pk)

    if conference.users_set.get(pk=request.user.pk) is None:
        raise Http404()

    if message_time_stamp != 0:
        link = get_object_or_404(ConferenceUserLink, user=request.user, conference=conference)
        link.last_message_date = message_time_stamp
        link.save()
        _messages = conference.get_messages_younger_then(message_time_stamp)
    else:
        _messages = conference.get_messages()

    json_response = [{'sender': m.sender.username, 'time_stamp': m.time_stamp, 'message': m.message} for m in _messages]
    return JsonResponse(json_response, safe=False)


@csrf_protect
@login_required
def messages_count(request):
    list_conference_pk = request.POST.get('list_conference_pk', None)

    if list_conference_pk is None:
        raise Http404()

    list_conference_pk = json.loads(list_conference_pk)

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
                    'users': conf.get_members_names(request.user),
                    'messages_count': conf.get_new_messages_count(request.user),
                }
            )
    return JsonResponse(json_response, safe=False)


@csrf_protect
@login_required
def users(request):
    conference_pk = request.POST.get('conference_pk', None)

    if conference_pk is None:
        raise Http404()

    conference = get_object_or_404(Conference, pk=conference_pk)
    json_response = conference.get_members_names_with_status()
    return JsonResponse(json_response, safe=False)


@csrf_protect
@login_required
def create_conference(request):
    username_list = request.POST.get('users', None)

    if username_list is None:
        raise Http404()

    username_list = json.loads(username_list)

    message = request.POST.get('message', None)
    _conference = Conference()
    _conference.save()

    time_stamp = timezone.now().timestamp()

    ConferenceUserLink.objects.bulk_create([ConferenceUserLink(conference=_conference, user=_user, last_message_date=time_stamp) for _user in User.objects.filter(username__in=username_list)])
    ConferenceUserLink.objects.create(conference=_conference, user=request.user, last_message_date=time_stamp)

    if message is not None and len(message) > 0:
        _conference.add_message(request.user, message)

    return JsonResponse({
        'conference_pk': _conference.pk,
        'users': username_list,
    }, safe=False)


@csrf_protect
@login_required
def send(request):
    conference_pk = request.POST.get('conference_pk', None)

    if conference_pk is None:
        Http404()

    message = request.POST.get('message', None)

    if message is None or len(message):
        Http404()

    conference = get_object_or_404(Conference, pk=conference_pk)
    conference.add_message(request.user, message)
    return HttpResponse('')


@csrf_protect
@login_required
def leave(request):
    conference_pk = request.POST.get('conference_pk', None)

    if conference_pk is None:
        raise Http404()

    conference = get_object_or_404(Conference, pk=conference_pk)
    conference.leave(request.user)
    return HttpResponse('')