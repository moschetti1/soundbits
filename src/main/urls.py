from django.urls import path 
from main import views


urlpatterns = [
    path("overview/", views.overview, name="overview"),
    path(
        "hx-get-log-details/<str:cheer_log_id>/", 
        views.hx_get_log_details, 
        name="hx-get-log-details"
    ),
    path(
        "hx-send-sfx-to-consumers/<str:sfx_request_id>/", 
        views.hx_send_sfx_to_consumers, 
        name="hx-send-sfx-to-consumers"
    ),
    path(
        "hx-generate-sfx/", 
        views.hx_generate_sfx, 
        name="hx-generate-sfx"
    ),
    path(
        "hx-sfx-list-for-cheer-log/<str:cheer_log_id>/",
        views.hx_sfx_list_for_cheer_log,
        name="hx-sfx-list-for-cheer-log"
    ),
    path(
        "alert-preferences/",
        views.alert_preferences_form,
        name="alert-preferences"
    ),
    path(
        "billing/",
        views.billing_view,
        name="billing"
    )
]
