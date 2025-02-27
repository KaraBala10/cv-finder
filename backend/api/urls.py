from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
    PublicUserProfileView,
    RegisterView,
    ResumeDeleteView,
    ResumeDownloadView,
    ResumeUploadView,
    ResumeViewPDF,
    UpdateProfileView,
    UserProfileView,
    VerifyEmailView,
)

urlpatterns = [
    path("signup/", RegisterView.as_view(), name="signup"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("profile/update/", UpdateProfileView.as_view(), name="update-profile"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("resume/upload/", ResumeUploadView.as_view(), name="resume-upload"),
    path(
        "resume/delete/<int:resume_id>/",
        ResumeDeleteView.as_view(),
        name="resume-delete",
    ),
    path(
        "resume/view/<str:username>/", ResumeViewPDF.as_view(), name="resume-view-pdf"
    ),
    path(
        "resume/download/<str:username>/",
        ResumeDownloadView.as_view(),
        name="resume-download",
    ),
    path(
        "profile/<str:username>/",
        PublicUserProfileView.as_view(),
        name="public-profile",
    ),
]
