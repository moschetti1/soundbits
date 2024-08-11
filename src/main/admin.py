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
    list_display = ["timestamp","cheer_event_log", "status", "is_metered", "has_recorded_usage"]

    def get_ordering(self, request):
        return ['-timestamp']

    def has_recorded_usage(self, obj):
        return bool(obj.usage_record_id)
    has_recorded_usage.boolean = True


admin.site.register(SoundEffectRequest, SoundEffectRequestAdmin)