from tornado.web import RequestHandler, Application, url
from tornado.gen import coroutine, Task
from tornado.httpclient import AsyncHTTPClient
from sockjs.tornado import SockJSConnection
from tornadoredis.pubsub import SockJSSubscriber
from tornadoredis import Client
from my_site import settings

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
    @coroutine
    def get(self):
        http = AsyncHTTPClient()
        response = yield http.fetch(url)

        self.write("Привет из Торнадо!")

class ChatWSConnectionHandler(SockJSConnection):
    def __init__(self, *args, **kwargs):
        super(ChatWSConnectionHandler, self).__init__(*args, **kwargs)

        self.redis_client = None
        self.django_user = None
        self.django_session = None

        self.setup_listener()

    @coroutine
    def setup_listener(self):
        self.redis_client = Client(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            password=getattr(settings, 'REDIS_PASSWORD', None),
            connection_pool=getattr(settings, 'REDIS_CONNECTION_POOL', None),
            unix_socket_path=getattr(settings, 'REDIS_UNIX_SOCKET_PATH', None)
        )

        yield Task(
            self.redis_client
        )

    def on_open(self, info):
        self.django_session = get_session(info.get_cookie('sessionid').value)
        self.django_user = get_user(self.django_session)

        self.redis_client.connect()
        self.redis_client.subscribe()
        self.subscription.subscribe("u-{u_name}".format(u_name=self.django_user.username), self)
        self.subscription.on_message()

    def on_message(self, message):
        # Broadcast message
        self.broadcast(self.participants, message)

    def on_close(self):
        # Remove client from the clients list and broadcast leave message
        self.participants.remove(self)

        self.broadcast(self.participants, "Someone left.")


application = Application([
    url(r"/", MainHandler),
])
