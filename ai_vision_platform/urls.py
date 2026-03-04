"""
URL configuration for ai_vision_platform project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from caption_app import views

urlpatterns = [

    path("admin/", admin.site.urls),

    # Django authentication
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/profile/", views.profile, name="accounts_profile"),

    # Main application routes
    path("", include("caption_app.urls")),

    # API routes
    path("api/", include("caption_app.urls")),
]

# Serve media files (important for Render)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
