# middleware.py

from django.shortcuts import redirect
from django.conf import settings
import re

EXEMPT_URLS = [re.compile(settings.LOGIN_URL.lstrip('/'))]
EXEMPT_URLS += [re.compile('logout/')]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        assert hasattr(request, 'user')
        path = request.path_info.lstrip('/')

        if not request.user.is_authenticated:
            if not any(url.match(path) for url in EXEMPT_URLS):
                return redirect(settings.LOGIN_URL)
        return self.get_response(request)
