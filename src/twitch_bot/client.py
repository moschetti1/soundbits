import json
import requests

from django.conf import settings
import twitch_bot.exceptions as exceptions

class TwitchClient:

    def __init__(self, client_id, secret, app_auth=True):
        self.base_url = "https://api.twitch.tv/helix/"
        self.client_id = client_id
        self.secret = secret
        self.access_token = self._get_access_token() if app_auth else self._get_user_access_token()
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Client-Id": self.client_id,
        }

    def _get_access_token(self):
        """
        Tries to get an access token for the app 
        Returns:
        - access_token: string
        Raises:
        - TwitchAuthenticationFailed
        """
        oauth_endpoint = "https://id.twitch.tv/oauth2/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.secret,
            "grant_type": "client_credentials"
        }
        r = requests.post(oauth_endpoint, payload)
        if not r.status_code in [200, 201]:
            raise exceptions.TwitchAuthenticationFailed
        return r.json()["access_token"]

    def _get_user_access_token(self, authorization_code):
        oauth_endpoint = "https://id.twitch.tv/oauth2/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.get("TWITCH_REDIRECT_URI")
        }
        r = requests.post(oauth_endpoint, payload)
        if not r.status_code in [200, 201]:
            raise exceptions.TwitchAuthenticationFailed
        return r.json()["access_token"]

    def _fetch_users_eventsubs(self, user_id):
        endpoint = self.base_url + "eventsub/subscriptions"

        payload = {
            "broadcaster_user_id": user_id
        }
        r = requests.get(endpoint, params=payload, headers=self.headers)
        if r.status_code != 200:
            raise exceptions.TwitchFetchSubscriptionsFailed
        return r.json()["data"]

    def create_eventsub(self, event_type:str, twitch_user_id: str) -> dict:
        endpoint = self.base_url + "eventsub/subscriptions"

        payload = {
            "type": event_type,
            "version": "1",
            "condition": {
                "broadcaster_user_id": twitch_user_id
            },
            "transport": {
                "method": "webhook",
                "callback": settings.TWITCH_WEBHOOK_CALLBACK,
                "secret": settings.TWITCH_WEBHOOK_SECRET
            }
        }
        
        r = requests.post(endpoint, json=payload, headers=self.headers)
        print(r.json())
        if r.status_code != 202:
            raise exceptions.TwitchEventSubCreationFailed

        return r.json()
       
    def delete_eventsub(self, user_id, event_type):
        endpoint = self.base_url + "eventsub/subscriptions"
        eventsubs = self._fetch_users_eventsubs(user_id)
        eventsubs_to_delete = [e for e in eventsubs if e["type"] == event_type]

        for event in eventsubs_to_delete:
            r = requests.delete(endpoint, params={"id": event["id"]}, headers=self.headers)
            if r.status_code != 204:
                raise exceptions.TwitchEventSubDeleteFailed

        return None


def elevenlabs_create_sfx(message, duration_seconds=4):
    url = settings.ELEVENLABS_SFX_ENDPOINT
    headers = {
        "Content-Type": "application/json",
        "Xi-Api-Key": settings.ELEVENLABS_API_KEY
    }
    payload = {
        "text": message,
        "duration_seconds": duration_seconds,
        "prompt_influence": 0.3
    }

    r = requests.post(url, json=payload, headers=headers)
    if 200 > r.status_code or r.status_code >= 300:
        raise exceptions.ElevenLabsApiError
        
    return r