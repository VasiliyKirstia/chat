from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from chat.models import *
from django.utils.decorators import method_decorator
import json

from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from redis import StrictRedis
from my_site import settings

_redis = StrictRedis(
    host=getattr(settings, 'REDIS_HOST', 'localhost'),
    port=getattr(settings, 'REDIS_PORT', 6379),
    db=getattr(settings, 'REDIS_DB', 0),
    password=getattr(settings, 'REDIS_PASSWORD', None),
    socket_timeout=getattr(settings, 'REDIS_SOCKET_TIMEOUT', None),
    connection_pool=getattr(settings, 'REDIS_CONNECTION_POOL', None),
    charset=getattr(settings, 'REDIS_CHARSET', 'utf-8'),
    errors=getattr(settings, 'REDIS_ERRORS', 'strict'),
    unix_socket_path=getattr(settings, 'REDIS_UNIX_SOCKET_PATH', None)
)

# название каналов для конференций - 'с-<conf_id>'
# название каналов для каждого пользователя - 'u-<username>'


class HomeView(TemplateView):
    template_name = "chat/index.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['users_list'] = User.objects.all().exclude(pk=self.request.user.pk)
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(HomeView, self).dispatch(*args, **kwargs)


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
def connect(request):
    conference_pk = request.POST.get('conference_pk', None)

    if conference_pk is None:
        raise Http404()

    last_message_ts = request.POST.get('time_stamp', None)

    if conference_pk is None:
        raise Http404()

    conference = get_object_or_404(Conference, pk=conference_pk)

    if conference.users_set.get(pk=request.user.pk) is None:
        raise Http404()

    link = ConferenceUserLink.objects.get(conference=conference, user=request.user)
    print(conference.messages.objects.latest('time_stamp').time_stamp)
    link.last_message_date = conference.messages.objects.latest('time_stamp').time_stamp
    link.save()

    _redis.publish("u-{u_name}".format(u_name=request.user.username), json.dumps(
        {
            'action': 'open',
            'channel': "c-{conf_id}".format(conf_id=conference.pk),
        }
    ))

    return JsonResponse({
        'conference_pk': conference_pk,
        'message_list': [{
                             'sender': message.sender,
                             'message': message.message,
                             'time_stamp': message.time_stamp,
                         } for message in conference.get_messages_younger_then(last_message_ts)]
    }, safe=False)


@csrf_protect
@login_required
def create_conference(request):
    username_list = request.POST.get('users', None)

    if username_list is None:
        raise Http404()

    message = request.POST.get('message', None)

    if message is None or len(message) == 0:
        raise Http404()

    username_list = json.loads(username_list)
    username_list.append(request.user.username)

    _conference = Conference()
    _conference.save()

    time_stamp = timezone.now().timestamp()

    ConferenceUserLink.objects.bulk_create(
        [ConferenceUserLink(conference=_conference, user=_user, last_message_date=time_stamp) for _user in
         User.objects.filter(username__in=username_list)])
    ConferenceUserLink.objects.create(conference=_conference, user=request.user, last_message_date=time_stamp)

    _conference.add_message(request.user, message)

    for username in username_list:
        _redis.publish("u-{u_name}".format(u_name=username), json.dumps(
            {
                'action': 'conference',
                'conference_pk': _conference.pk,
                'messages_count': 1,
                'username_list': username_list,
            }
        ))

    return HttpResponse('')


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

    if conference.users_set.get(pk=request.user.pk) is None:
        raise Http404()

    timestamp = conference.add_message(request.user, message)

    _redis.publish("c-{conf_id}".format(conf_id=conference.pk), json.dumps(
        {
            'action': 'message',
            'username': request.user.username,
            'message': message,
            'timestamp': timestamp,
        }
    ))

    return HttpResponse('')


@csrf_protect
@login_required
def leave(request):
    conference_pk = request.POST.get('conference_pk', None)

    if conference_pk is None:
        raise Http404()

    conference = get_object_or_404(Conference, pk=conference_pk)
    was_deleted = conference.leave(request.user)
    if not was_deleted:
        _redis.publish("c-{conf_id}".format(conf_id=conference.pk), json.dumps(
            {
                'action': 'leave',
                'conference_pk': conference.pk,
                'username': request.user.username,
            }
        ))

    _redis.publish("u-{u_name}".format(u_name=request.user.username), json.dumps(
        {
            'action': 'close',
            'channel': "c-{conf_id}".format(conf_id=conference.pk),
        }
    ))

    return HttpResponse('')