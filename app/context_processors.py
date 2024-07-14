""" Context Processor keys """

from django.conf import settings

def base_css_version(request):
    return {'BASE_CSS_VERSION': settings.BASE_CSS_VERSION}
