import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from billing.constants import SubscriptionPlanOptions
# Create your models here.



class Broadcaster(AbstractUser):
    id = models.UUIDField(
        default=uuid.uuid4,
        primary_key=True,
        editable=False
    )
    lemon_customer_id = models.TextField(null=True, blank=True)
    lemon_subscription_item_id = models.TextField(null=True, blank=True)
    max_free_runs = models.IntegerField(default=15)
    billing_plan = models.CharField(
        max_length=10, 
        choices=SubscriptionPlanOptions.PLANS_LIST, 
        default=SubscriptionPlanOptions.PLAN_DEFAULT
    )

    @property
    def has_lemon_billing_setup(self):
        return bool(self.lemon_customer_id) and bool(self.lemon_subscription_item_id)