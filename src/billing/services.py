import hmac
import hashlib
import logging
from datetime import datetime

from django.conf import settings

from main.models import SoundEffectRequest
from main.constants import DONE_STATUS
from billing.constants import SubscriptionPlanOptions, LemonSubscriptionEvents, LEMON_WEBHOOK_SIGNATURE_HEADER, LEMON_WEBHOOK_EVENT_NAME_HEADER
from .client import Lemon, LemonUsageUpdateError


logger = logging.getLogger('django')

class BillingService:


    @staticmethod
    def _free_runs_count(user):
        return SoundEffectRequest.objects.filter(
                cheer_event_log__internal_broadcaster_user=user,
                status=DONE_STATUS,
                is_metered=False
            ).count()

    @staticmethod
    def _is_valid_billing_status(user):
        """Checks that the user is in a plan that allows new runs/generations."""
        if user.billing_plan == SubscriptionPlanOptions.FREE_PLAN:
            runs_count = BillingService._free_runs_count(user)
            return runs_count < user.max_free_runs

        return user.billing_plan == SubscriptionPlanOptions.PAID_PLAN

    @staticmethod
    def _has_metered_usage(user):
        return user.billing_plan == SubscriptionPlanOptions.PAID_PLAN
        
    @staticmethod    
    def enable_user_subscription(user):
        user.billing_plan = SubscriptionPlanOptions.PAID_PLAN
        user.save()
        return user

    @staticmethod
    def cancel_user_plan(user):
        user.billing_plan = SubscriptionPlanOptions.CANCELED_PLAN
        user.save()
        return user

    @staticmethod
    def update_billing_setup(user, subscription_item_id=False, customer_id=False):
        if not subscription_item_id and not customer_id:
            return user
        
        if subscription_item_id:
            user.lemon_subscription_item_id = subscription_item_id
        if customer_id:
            user.lemon_customer_id = customer_id

        user.save()
        
        return user

    @staticmethod
    def create_usage_record(user, sound_effect_request):
        client = Lemon(settings.LEMON_API_KEY)
        if not user.has_lemon_billing_setup:
            pass
        
        try:
            r = client.create_usage_record(subscription_item_id=user.lemon_subscription_item_id)
        except LemonUsageUpdateError:
            logger.error("Failed to create Usage Record for Sfx: " + str(sound_effect_request.id))
            return None
        sound_effect_request.usage_record_id = r["data"]["id"]
        sound_effect_request.save()
        return r

    @staticmethod
    def get_current_period_usage(user):
        client = Lemon(settings.LEMON_API_KEY)
        r = client.get_current_usage(user.lemon_subscription_item_id)
        context = {
            "period_start": datetime.fromisoformat(r["meta"]["period_start"]),
            "period_end": datetime.fromisoformat(r["meta"]["period_end"]),
            "quantity": r["meta"]["quantity"],
        }
        return context

    @staticmethod
    def get_user_customer_object(user):
        client = Lemon(settings.LEMON_API_KEY)
        r = client.get_customer_object(user.lemon_customer_id)
        context = {
            "customer_portal": r["data"]["attributes"]["urls"]["customer_portal"]
        }
        return context


class LemonWebhookHandler:

    def __init__(self, request, secret):
        self.headers = request.headers
        self.body = request.body
        self.secret = secret 

    def is_verified(self):
        signature = self.headers.get(LEMON_WEBHOOK_SIGNATURE_HEADER)
        digest = hmac.new(self.secret.encode(), self.body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature)

    def get_event_type(self):
        event_type = self.headers[LEMON_WEBHOOK_EVENT_NAME_HEADER]
        return event_type, event_type in LemonSubscriptionEvents.ACCEPTED_EVENTS


