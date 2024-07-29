from django.contrib import admin
from .models import AlertPreferences, CheerEventLogEntry, SoundEffectRequest



class AlertPreferencesAdmin(admin.ModelAdmin):
    list_display = ["user", "eventsub_setted_up"]

    def eventsub_setted_up(self, obj):
        return obj.cheer_eventsub_id != None
    eventsub_setted_up.boolean = True

admin.site.register(AlertPreferences, AlertPreferencesAdmin)


class CheerLogAdmin(admin.ModelAdmin):
    list_display = ["broadcaster_user_name", "user_name", "bits", "status"]

admin.site.register(CheerEventLogEntry, CheerLogAdmin)


class SoundEffectRequestAdmin(admin.ModelAdmin):
    list_display = ["cheer_event_log", "status"]

admin.site.register(SoundEffectRequest)