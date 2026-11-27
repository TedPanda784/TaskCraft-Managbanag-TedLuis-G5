from django.urls import path

from .views import ProfileView, SignUpView, TaskCraftLoginView, TaskCraftLogoutView


urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", TaskCraftLoginView.as_view(), name="login"),
    path("logout/", TaskCraftLogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
