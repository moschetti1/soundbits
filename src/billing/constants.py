

class SubscriptionPlanOptions():
    FREE_PLAN = "Free"
    PAID_PLAN = "Creator"
    CANCELED_PLAN = "Canceled"

    PLAN_DEFAULT = FREE_PLAN

    PLANS_LIST = [
        [FREE_PLAN, "Free account"],
        [PAID_PLAN, "Creator account"],
        [CANCELED_PLAN, "Canceled subscription"]
    ]

LEMON_WEBHOOK_SIGNATURE_HEADER = "X-Signature"
LEMON_WEBHOOK_EVENT_NAME_HEADER = "X-Event-Name"


class LemonSubscriptionEvents():

    CREATED = "subscription_created"
    RESUMED = "subscription_resumed"
    UNPAUSED = "subscription_unpaused"

    EXPIRED = "subscription_expired"
    PAUSED = "subscription_paused"
    CANCELED = "subscription_cancelled"

    ENABLED_EVENTS = [
        CREATED, 
        RESUMED, 
        UNPAUSED
    ] 

    CANCEL_EVENTS = [
        EXPIRED,
        PAUSED,
        CANCELED
    ]

    ACCEPTED_EVENTS = ENABLED_EVENTS + [EXPIRED, PAUSED, CANCELED]