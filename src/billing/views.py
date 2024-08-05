import json
import logging
from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponse
from django.conf import settings 
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST 

from .services import LemonWebhookHandler, BillingService
from .constants import LemonSubscriptionEvents
# Create your views here.

logger =  logging.getLogger('django')

@csrf_exempt
@require_POST
def lemon_webhook(request):
    User = get_user_model()
    body = json.loads(bytes.decode(request.body))
    handler = LemonWebhookHandler(request, settings.LEMON_WEBHOOK_SECRET)

    if not handler.is_verified():
        logger.info("Invalid lemon signature on webhook call.")
        return HttpResponseForbidden("Signatures don't match")
 
    event_type, valid_event_type = handler.get_event_type()
    if not valid_event_type:
        logger.info("Invalid lemon event type on webhook call.")
        return HttpResponse()

    try:
        internal_user_id = body["meta"]["custom_data"]["user_id"]
        user = User.objects.get(id=internal_user_id)
    except:
        logger.warning("Invalid internal user id on lemon webhook call.")
        return HttpResponse()

    lemon_customer_id = body["data"]["attributes"]["customer_id"]
    if not user.has_lemon_billing_setup:
        BillingService.update_billing_setup(
            user,
            subscription_item_id = body["data"]["attributes"]["first_subscription_item"]["id"],
            customer_id = lemon_customer_id
        )

    if event_type in LemonSubscriptionEvents.ENABLED_EVENTS:
        user = BillingService.enable_user_subscription(user)
        
    elif event_type in LemonSubscriptionEvents.CANCEL_EVENTS:
        BillingService.cancel_user_plan(user)    

    return HttpResponse()
    