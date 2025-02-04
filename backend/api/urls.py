from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    RegisterView,
    UpdateProfileView,
    UserProfileView,
)

urlpatterns = [
    path("signup/", RegisterView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("profile/update/", UpdateProfileView.as_view(), name="update-profile"),
]
