from tornado.web import RequestHandler, Application, url
from tornado.gen import coroutine, Task, engine
from tornado.httpclient import AsyncHTTPClient
from sockjs.tornado import SockJSConnection, SockJSRouter
from tornadoredis.pubsub import SockJSSubscriber
from tornadoredis import Client
from my_site import settings

import json
import django
from django.utils.importlib import import_module
from django.conf import settings as csettings

_engine = import_module(csettings.SESSION_ENGINE)
_online_users_list = []

def get_session(session_key):
    return _engine.SessionStore(session_key)


def get_user(session):
    class Dummy(object):
        pass

    django_request = Dummy()
    django_request.session = session

    return django.contrib.auth.get_user(django_request)


class MainHandler(RequestHandler):
    def get(self):
        print('\nget\n')
        self.write("Привет из Торнадо!")


class ChatWSConnectionHandler(SockJSConnection):
    def __init__(self, *args, **kwargs):
        print('\ninit\n')
        super(ChatWSConnectionHandler, self).__init__(*args, **kwargs)

        self.django_user = None
        self.django_session = None

        self.redis_client = Client(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            password=getattr(settings, 'REDIS_PASSWORD', None),
            connection_pool=getattr(settings, 'REDIS_CONNECTION_POOL', None),
            unix_socket_path=getattr(settings, 'REDIS_UNIX_SOCKET_PATH', None)
        )

    @coroutine
    def on_open(self, info):
        print('\nonopen\n')
        self.django_session = get_session(info.get_cookie('sessionid').value)
        self.django_user = get_user(self.django_session)

        _online_users_list.append(self.django_user)

        self.redis_client.connect()
        yield Task(self.redis_client.subscribe, "u-{u_name}".format(u_name=self.django_user.username))
        self.redis_client.listen(self.on_redis_message)

    def on_message(self, message):
        print('\nonmessage\n')
        command = json.loads(message)

        if command == 'get_users_online':
            self.send(json.dumps(_online_users_list))

    def on_close(self):
        print('\nonclose\n')
        _online_users_list.remove(self.django_user)

    @coroutine
    def on_redis_message(self, msg):
        if msg.kind == 'message':
            message = json.loads(msg.body)

            if message['action'] == 'message':
                self.send(msg.body)

            elif message['action'] == 'open':
                yield Task(self.redis_client.subscribe, message['channel'])

            elif message['action'] == 'conference':
                self.send(msg.body)

            elif message['action'] == 'close':
                yield Task(self.redis_client.unsubscribe, message['channel'])

            elif message['action'] == 'leave':
                self.send(msg.body)

ChatRouter = SockJSRouter(ChatWSConnectionHandler, '/chat')

application = Application(ChatRouter.urls)
