class TwitchAuthenticationFailed(Exception):
    "Raised when App credentials fail to authenticate"
    pass

class TwitchFetchSubscriptionsFailed(Exception):
    "Raised when App credentials fail to authenticate"
    pass

class TwitchEventSubCreationFailed(Exception):
    "Raised when an EventSub subscription request fails"
    pass

class TwitchEventSubDeleteFailed(Exception):
    "Raised when an attempt to delete an EventSub fails"
    pass
