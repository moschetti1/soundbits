import uuid
import os 
import logging

from django.db import models
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from twitch_bot.exceptions import TwitchEventSubCreationFailed

from .constants import (
    SOUND_EFFECT_REQUEST_STATUS_OPTIONS, 
    CHEER_EVENT_LOG_STATUS_OPTIONS,
    TWITCH_CHEER_EXTERNAL_REFERENCE,
    NEW_STATUS,
    DONE_STATUS
)
from allauth.account.signals import user_signed_up

from twitch_bot.client import TwitchClient

logger = logging.getLogger('django')

class CheerEventLogEntry(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, 
        primary_key=True, 
        editable=False
    )
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    internal_broadcaster_user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    status = models.CharField(choices=CHEER_EVENT_LOG_STATUS_OPTIONS, default=NEW_STATUS, max_length=1)
    #twitch notification fields
    twitch_message_id = models.TextField(null = False)
    is_anonymous = models.BooleanField(default=False)
    user_id = models.CharField(max_length=50, null=True, blank=True)
    user_login = models.CharField(max_length=150, null=True, blank=True)
    user_name = models.CharField(max_length=150, null=True, blank=True)
    broadcaster_user_id = models.CharField(max_length=50)
    broadcaster_user_login = models.CharField(max_length=150)
    broadcaster_user_name = models.CharField(max_length=150)
    message = models.TextField()
    bits = models.IntegerField(default=0)

    def __str__(self):
        return str(self.broadcaster_user_name)

    class Meta:
        ordering = ["-timestamp"]

#if we want to support more alert types, a unique model for preferences based on each type might be necessary. for now this is all we need. 
class AlertPreferences(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, 
        primary_key=True, 
        editable=False
    )
    user = models.OneToOneField(
        get_user_model(), 
        on_delete=models.CASCADE
    )
    match_command = models.BooleanField(default=False)
    command_string = models.CharField(
        max_length=20, 
        default="$fx"
    )
    auto_generate = models.BooleanField(default=True)
    auto_play = models.BooleanField (default=True)
    match_bits = models.BooleanField(
        default=True, 
        help_text="If enabled, the match ammount has to be exact to generate a sfx. Otherwise, anything over the set bit ammount will generate a sfx.")
    min_bits = models.IntegerField(default=200)
    cheer_eventsub_id = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username + " preferences"

class SoundEffectRequest(models.Model):

    def upload_sfx_file(instance, filename):
        return os.path.join(
            "sfx_files", 
            str(instance.cheer_event_log.internal_broadcaster_user.id), 
            str(instance.cheer_event_log.id), 
            filename
        )
    
    id = models.UUIDField(
        default=uuid.uuid4, 
        primary_key=True, 
        editable=False
    )
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    cheer_event_log = models.ForeignKey(CheerEventLogEntry, on_delete=models.CASCADE)
    status = models.CharField(
        choices=SOUND_EFFECT_REQUEST_STATUS_OPTIONS,
        max_length=1,
        default=NEW_STATUS
    )
    generated_file = models.FileField(upload_to=upload_sfx_file, null=True, blank=True)
    failed_reason = models.TextField(blank=True)
    is_metered = models.BooleanField(default=False)
    usage_record_id = models.TextField(null=True, blank=True)

    @property
    def has_usage_record(self):
        return bool(self.usage_record_id)

    class Meta:
        ordering = ["-timestamp"]


@receiver(user_signed_up)
def create_settings_for_new_user(request, user, **kwargs):
    client = TwitchClient(settings.TWITCH_APP_CLIENT_ID, settings.TWITCH_APP_CLIENT_SECRET)
    socialaccount = user.socialaccount_set.get(provider="twitch") 
    twitch_uid = socialaccount.uid
    try:
        eventsub = client.create_eventsub(TWITCH_CHEER_EXTERNAL_REFERENCE, str(twitch_uid))
        eventsub_id = eventsub["data"][0]["id"]
    except TwitchEventSubCreationFailed:
        logger.error("Twitch Setup: Failed to create eventsub")
        eventsub_id = None
    AlertPreferences.objects.create(user=user, cheer_eventsub_id=eventsub_id)

@receiver(post_save, sender=SoundEffectRequest)    
def update_cheer_log_status(sender, instance, created, *args, **kwargs):
    cheer_log = instance.cheer_event_log

    if cheer_log.status == DONE_STATUS or instance.status == NEW_STATUS:
        return None
    
    cheer_log.status = instance.status
    cheer_log.save()