from django import forms
from django.core.exceptions import ValidationError

from.models import AlertPreferences, SoundEffectRequest

class AlertPreferencesForm(forms.ModelForm):
    class Meta:
        model = AlertPreferences
        fields = "__all__"
        exclude = ["user",]

    def clean_min_bits(self):
        data = self.cleaned_data["min_bits"]
        if data <= 0:
            raise ValidationError("Can't be less than 0")

        return data


class GenerateSfxForm(forms.ModelForm):
    class Meta:
        model = SoundEffectRequest
        fields = ["cheer_event_log"]

    