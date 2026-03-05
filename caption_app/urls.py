```python
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [

    # ==========================================
    # MAIN PAGES
    # ==========================================

    path('', views.index, name='index'),

    path('register/', views.register, name='register'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('upload/', views.upload, name='upload'),

    path('history/', views.history, name='history'),

    path('profile/', views.profile, name='profile'),


    # ==========================================
    # AI PROCESSING
    # ==========================================

    path('generate/', views.generate_caption_view, name='generate_caption'),


    # ==========================================
    # DEBUG ENDPOINT
    # ==========================================

    path('debug/caption-test/', views.debug_caption_test, name='debug_caption_test'),

]


# ==========================================
# MEDIA FILES (IMAGE + AUDIO)
# ==========================================

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```
