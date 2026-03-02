import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'ai_vision_platform.settings'
import django
django.setup()
from django.urls import get_resolver
res = get_resolver()

def walk(patterns, prefix=''):
    for p in patterns:
        try:
            pat = p.pattern._route
        except Exception:
            pat = repr(p)
        print(prefix + pat + ' -> ' + p.__class__.__name__)
        if hasattr(p, 'url_patterns'):
            walk(p.url_patterns, prefix + '  ')

walk(res.url_patterns)
