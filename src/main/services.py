import hmac
import hashlib
import after_response
import json
import logging 
from django.core.files.base import ContentFile, File
from allauth.socialaccount.models import SocialAccount
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from secrets import compare_digest
from twitch_bot.client import elevenlabs_create_sfx
from .models import SoundEffectRequest, CheerEventLogEntry, AlertPreferences
from twitch_bot.constants import *
from twitch_bot.exceptions import ElevenLabsApiError
from .constants import NEW_STATUS, IGNORED_STATUS, FAILED_STATUS, DONE_STATUS
from billing.services import BillingService

logger = logging.getLogger('django')


class TwitchWebhookHandler:

    def __init__(self, request, secret):
        self.headers = request.headers
        self.body = request.body
        self.secret = secret 


    def is_verified(self):
        message_id = self.headers[WEBHOOK_ID_HEADER]
        message_timestamp = self.headers[WEBHOOK_TIMESTAMP_HEADER]
        message_signature = self.headers[WEBHOOK_SIGNATURE_HEADER]
        
        local_message = message_id + message_timestamp + bytes.decode(self.body, 'utf-8')
        local_message_bytes = bytes(local_message, 'utf-8')
        key = bytes(self.secret, 'utf-8')
        local_message_signature = "sha256=" + hmac.new(key, local_message_bytes, hashlib.sha256).hexdigest()

        return compare_digest(bytes(message_signature, 'utf-8'), bytes(local_message_signature, 'utf-8'))


    def is_challenge(self):
        event_type = self.headers[WEBHOOK_TYPE_HEADER]
        return event_type == "webhook_callback_verification"


    def is_duplicate(self):
        if self.headers.get(WEBHOOK_RESEND_HEADER, False):
            return True
        return False

class SoundEffectRequestService:

    @staticmethod
    def _send_event_to_consumers(sfx_source, user_id, cheer_log):
        channel_layer = get_channel_layer()
        event = {
            "type": "play_sfx",
            "sfx_source": sfx_source,
            "username": cheer_log.user_name if not cheer_log.is_anonymous else "Anonymous",
            "prompt": cheer_log.message,
            "bits": cheer_log.bits
        }
        async_to_sync(channel_layer.group_send)(
            user_id, event
        )


    @staticmethod
    def _validate_cheer_with_preferences(alert_preferences, cheer_event_data):
        command_string_length = len(alert_preferences.command_string)
        command_validated = True
        bits_validated = cheer_event_data["bits"] >= alert_preferences.min_bits

        if alert_preferences.match_command and command_string_length:
            command_validated = alert_preferences.command_string != "" and cheer_event_data["message"].startsWith(
                alert_preferences.command_string, 
                0, 
                command_string_length
            )

        if alert_preferences.match_bits:
            bits_validated = cheer_event_data["bits"] == alert_preferences.min_bits

        return command_validated and bits_validated
        

    @staticmethod
    def save_cheer_event(user, alert_preferences, cheer_event_data, twitch_message_id):
        meets_requirements = SoundEffectRequestService._validate_cheer_with_preferences(
            alert_preferences, 
            cheer_event_data
        )
        status = NEW_STATUS if meets_requirements else IGNORED_STATUS

        cheer_event_log = CheerEventLogEntry.objects.create(
            internal_broadcaster_user=user, 
            twitch_message_id=twitch_message_id,
            status=status,
            **cheer_event_data
        )
        return cheer_event_log, meets_requirements
    

    @staticmethod
    @after_response.enable
    def generate_sfx(user, cheer_event_log, send_to_consumers=True):
        
        if not BillingService._is_valid_billing_status(user):
            sfx_request = SoundEffectRequest.objects.create(
                cheer_event_log=cheer_event_log,
                status=FAILED_STATUS,
                is_metered=False,
                failed_reason="Not enough credits. Upgrade billing plan."
            )
            return sfx_request
        
        try:
            response = elevenlabs_create_sfx(
                cheer_event_log.message,
                duration_seconds=4
            )
        except ElevenLabsApiError:
            logger.error("Sound Effect Generation: API call to elevenlabs failed.")
            sfx_request = SoundEffectRequest.objects.create(
                cheer_event_log=cheer_event_log,
                status=FAILED_STATUS,
                is_metered=False,
                failed_reason="Failed trying to generate sfx."
            )
            return sfx_request

        file = response.content 
        
        is_metered = BillingService._has_metered_usage(user)
        sfx_request = SoundEffectRequest.objects.create(
            cheer_event_log=cheer_event_log,
            status=DONE_STATUS,
            is_metered = is_metered
        )
        sfx_request.generated_file.save(
            f"{sfx_request.id}.mp3", 
            ContentFile(file), 
            save=True
        )

        if send_to_consumers:
            SoundEffectRequestService._send_event_to_consumers(
                sfx_request.generated_file.url, 
                str(user.id),
                cheer_event_log
            )

        if is_metered:    
            BillingService.create_usage_record(user, sfx_request)

        return sfx_request


    