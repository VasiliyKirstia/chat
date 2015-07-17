import json
from django.contrib.auth.models import User

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from research_work.models import *


class HomeView(TemplateView):
    template_name = "research_work/index.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['users_list'] = User.objects.all().exclude(pk=self.request.user.pk)
        return context


@csrf_exempt
@login_required
def send_pack(request):
    """
    data:{
        key_press[
            {
                key_code
                time
            }
        ]
        key_release[
            {
                key_code,
                time
            }
        ]
    }
    """
    data = json.loads(request.POST.get('data'))

    _subject, _ = Subject.objects.get_or_create(name=request.user.pk)

    _pack = Pack.objects.create(subject=_subject)

    KeyPressTime.objects.bulk_create(
        [KeyPressTime(key=my_dict['key_code'], time=my_dict['time'], pack=_pack) for my_dict in data['key_press']]
    )

    KeyReleaseTime.objects.bulk_create(
        [KeyPressTime(key=my_dict['key_code'], time=my_dict['time'], pack=_pack) for my_dict in data['key_release']]
    )

    return HttpResponse('')



























