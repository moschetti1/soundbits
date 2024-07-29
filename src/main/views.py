import json

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden, HttpResponse, StreamingHttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST 
from django_eventstream import send_event
from django.contrib.auth import get_user_model

from allauth.socialaccount.models import SocialAccount
from .models import AlertPreferences, SoundEffectRequest, CheerEventLogEntry
from .forms import AlertPreferencesForm, GenerateSfxForm
from .services import TwitchWebhookHandler, SoundEffectRequestService


#Public views (Webhook & Overlay)
@csrf_exempt
@require_POST
def twitch_eventsub_callback(request):
    body = json.loads(bytes.decode(request.body))
    request_handler = TwitchWebhookHandler(
        request, 
        settings.TWITCH_WEBHOOK_SECRET
    )

    if not request_handler.is_verified():
        return HttpResponseForbidden("Signatures don't match")

    if request_handler.is_challenge():
        return HttpResponse(
            body["challenge"], 
            content_type="text/plain"
        )

    notification_id = body["subscription"]["id"]
    notification_type = body["subscription"]["type"]
    notification_data = body["event"]
    social_account_id = notification_data["broadcaster_user_id"]

    if request_handler.is_duplicate():
        if CheerEventLogEntry.objects.filter(twitch_message_id=notification_id).exists():
            return HttpResponse()
    
    if not notification_type == "channel.cheer":
        return HttpResponse()
        
    try:
        social_user = SocialAccount.objects.get(uid=social_account_id)
        user = social_user.user
        alert_preferences = user.alertpreferences
    except:
        return HttpResponse()
    
    cheer_event_log, meets_requirements = SoundEffectRequestService.save_cheer_event(
        user, 
        alert_preferences, 
        notification_data,
        notification_id
    )
    
    if meets_requirements and alert_preferences.auto_generate:
        SoundEffectRequestService.generate_sfx.after_response(
            cheer_event_log, 
            send_to_consumers=alert_preferences.auto_play
        )

    return HttpResponse()


def broadcaster_overlay(request, user_id):
    socket_routing = "/ws/cheers/"
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    
    template_name = "overlay/main.html"
    context = {"socket_url": socket_routing + str(user_id) + "/"}

    return render(request, template_name, context)


#Dashboard views
@login_required
def overview(request):
    template_name = "dashboard/overview.html"
    logs = CheerEventLogEntry.objects.filter(internal_broadcaster_user=request.user)
    context = {"username": request.user.username, "logs": logs}
    return render(request, template_name, context)


@login_required
def hx_get_log_details(request, cheer_log_id):
    template_name = "dashboard/partials/log_details.html"
    cheer_log_object = get_object_or_404(CheerEventLogEntry, id=cheer_log_id)
    context = {"cheer_log": cheer_log_object}
    return render(request, template_name, context)


@login_required
@require_POST
def hx_generate_sfx(request):
    cheer_log_id = request.POST.get("cheer_log_id")

    template_name = "dashboard/partials/sfx_control.html"
    cheer_log_object = get_object_or_404(CheerEventLogEntry, id=cheer_log_id)
    sfx = SoundEffectRequestService.generate_sfx(
        cheer_log_object, 
        send_to_consumers=False
    )

    context = {"sfx_request": sfx}
    return render(request, template_name, context)

@login_required
def hx_send_sfx_to_consumers(request, sfx_request_id):
    sfx = get_object_or_404(SoundEffectRequest, id=sfx_request_id)
    
    if sfx.cheer_event_log.internal_broadcaster_user != request.user:
        return HttpResponseForbidden("You don't own this resource")
    
    broadcaster_settings = get_object_or_404(
        AlertPreferences, 
        user=request.user
    )
    
    SoundEffectRequestService._send_event_to_consumers(str(request.user.id), sfx.generated_file.url)

    return HttpResponse()


@login_required
def alert_preferences_form(request):
    alert_preferences = get_object_or_404(AlertPreferences, user=request.user)
    
    if request.method == "POST":
        template_name = "dashboard/partials/alert_preferences_form.html"
        form = AlertPreferencesForm(request.POST, instance=alert_preferences)
        
        if form.is_valid():
            messages.success(request, "Your preferences have been updated")
            form.save()
        else:
            messages.error(request, "There was an error saving the form.")

        context = {"form":form}
        return render(request, template_name, context)

    template_name = "dashboard/preferences.html"
    form = AlertPreferencesForm(instance=alert_preferences)
    context = {"form":form}

    return render(request, template_name, context)