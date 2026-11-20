from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import (
    CustomUserCreationForm,
    ProfileForm,
    TaskCraftAuthenticationForm,
)


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")
    success_message = "Your account was created. You can now log in."


class TaskCraftLoginView(LoginView):
    form_class = TaskCraftAuthenticationForm
    template_name = "registration/login.html"
    redirect_authenticated_user = True


class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("profile")
    success_message = "Your profile was updated."

    def get_object(self, queryset=None):
        return self.request.user
