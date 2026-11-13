from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "course",
            "phone_number",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "course", "phone_number")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class CampusConnectAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _("Invalid username or password."),
    }
