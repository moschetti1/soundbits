import logging
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
from .constants import (
    DONE_STATUS,
    FAILED_STATUS, 
    IGNORED_STATUS,
    NEW_STATUS,
)
from .services import TwitchWebhookHandler, SoundEffectRequestService
from billing.constants import SubscriptionPlanOptions
from billing.services import BillingService

logger =  logging.getLogger('django')

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
        logger.warning("Twitch webhook: signature mismatch on received event.")
        return HttpResponseForbidden("Signatures don't match")

    if request_handler.is_challenge():
        logger.info("Twitch webhook: challenge request received.")
        return HttpResponse(
            body["challenge"], 
            content_type="text/plain"
        )

    notification_id = body["subscription"]["id"]
    notification_type = body["subscription"]["type"]

    if request_handler.is_duplicate() and CheerEventLogEntry.objects.filter(twitch_message_id=notification_id).exists():
        logger.info("Twitch webhook: Duplicate event message already handled.")
        return HttpResponse()
    
    if not notification_type == "channel.cheer":
        logger.warning("Twitch webhook: unallowed event type.")
        return HttpResponse()

    notification_data = body["event"]
    social_account_id = notification_data["broadcaster_user_id"]    
    try:
        social_user = SocialAccount.objects.get(uid=social_account_id)
        user = social_user.user
        alert_preferences = user.alertpreferences
    except:
        logger.warning("Twitch webhook: Missing social account for twitch user.")
        return HttpResponse()
    
    cheer_event_log, meets_requirements = SoundEffectRequestService.save_cheer_event(
        user, 
        alert_preferences, 
        notification_data,
        notification_id
    )
    if meets_requirements and alert_preferences.auto_generate:
        SoundEffectRequestService.generate_sfx.after_response(
            user,
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
    context = {
        "username": request.user.username, 
        "logs": logs,
        "failed_status": FAILED_STATUS,
        "done_status": DONE_STATUS,
        "ignored_status": IGNORED_STATUS,
        "new_status": NEW_STATUS
        }

    if request.user.billing_plan == SubscriptionPlanOptions.FREE_PLAN:
        context.update({
            "used": BillingService._free_runs_count(request.user),
            "max_usage": request.user.max_free_runs
        })

    return render(request, template_name, context)


@login_required
def hx_get_log_details(request, cheer_log_id):
    template_name = "dashboard/partials/log_details.html"
    cheer_log_object = get_object_or_404(CheerEventLogEntry, id=cheer_log_id)
    context = {
        "cheer_log": cheer_log_object,
        "failed_status": FAILED_STATUS,
        "done_status": DONE_STATUS,
        "ignored_status": IGNORED_STATUS,
        "new_status": NEW_STATUS,
    }
    return render(request, template_name, context)


@login_required
@require_POST
def hx_generate_sfx(request):
    cheer_log_id = request.POST.get("cheer_log_id")

    toast_template_name = "dashboard/ui/toast.html"
    cheer_log_object = get_object_or_404(CheerEventLogEntry, id=cheer_log_id)
    SoundEffectRequestService.generate_sfx.after_response(
        request.user,
        cheer_log_object, 
        send_to_consumers=False
    )

    messages.success(request,"SFX generation started")

    return render(request, toast_template_name)

@login_required
def hx_sfx_list_for_cheer_log(request, cheer_log_id):
    query = SoundEffectRequest.objects.filter(
        cheer_event_log__id=cheer_log_id
    )
    template_name = "dashboard/partials/sfx_control_list.html"

    context = {
        "failed_status": FAILED_STATUS,
        "done_status": DONE_STATUS,
        "ignored_status": IGNORED_STATUS,
        "new_status": NEW_STATUS,
        "sfx_list": query
    }

    return render(request, template_name, context)


@login_required
def hx_send_sfx_to_consumers(request, sfx_request_id):
    template_name = "dashboard/ui/toast.html"
    sfx = get_object_or_404(SoundEffectRequest, id=sfx_request_id)
    
    if sfx.cheer_event_log.internal_broadcaster_user != request.user:
        return HttpResponseForbidden("You don't own this resource")
    
    broadcaster_settings = get_object_or_404(
        AlertPreferences, 
        user=request.user
    )
    
    SoundEffectRequestService._send_event_to_consumers(
        sfx.generated_file.url,
        str(request.user.id), 
        sfx.cheer_event_log
    )
    messages.success(request, "Sent sound effect to your overlay")
    return render(request, template_name)


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



@login_required
def billing_view(request):
    context = {
        "free_plan_constant": SubscriptionPlanOptions.FREE_PLAN,
        "period_start": False,
        "period_end": False,
        "quantity": 0,
        "customer_portal": settings.LEMON_CUSTOMER_PORTAL_URL
    }
    if request.user.billing_plan == SubscriptionPlanOptions.FREE_PLAN:
        context.update({
            "used": BillingService._free_runs_count(request.user)
        })

    elif request.user.billing_plan == SubscriptionPlanOptions.PAID_PLAN and request.user.has_lemon_billing_setup:
        try:
            current_usage = BillingService.get_current_period_usage(request.user)
            customer_portal = BillingService.get_user_customer_object(request.user)
            context.update(customer_portal)
            context.update(current_usage)
        except:
            logger.error(
                "Billing page: Failed to fetch current plan usage for user: {username}".format(
                    username=request.user.username
                )
            )

    
    return render(request, "dashboard/billing.html", context)