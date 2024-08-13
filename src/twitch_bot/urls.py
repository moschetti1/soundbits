from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from main import views
from .views import login_template, home, privacy_policy, terms_of_service, refund_policy
from billing import views as billing_views
urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path('accounts/', include("allauth.urls")),
    path("login/", login_template, name="login"),
    path("hooks/twitch/events/", views.twitch_eventsub_callback, name="twitch-hook"),
    path("hooks/lemon/events/", billing_views.lemon_webhook, name="lemon-webhook"),
    path("overlay/<str:user_id>/", views.broadcaster_overlay, name="overlay"),
    path("dashboard/", include(("main.urls", "main"), namespace="dashboard")),
    path("legal/refunds-policy/", refund_policy, name="refunds-policy"),
    path("legal/privacy-policy/", privacy_policy, name="privacy-policy"),
    path("legal/terms-of-service/", terms_of_service, name="terms-of-service"),
]


if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)