import imghdr
from datetime import timedelta

import redis
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import JsonResponse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser, Profile, Resume
from .serializers import ProfileSerializer, ResumeSerializer, UserSerializer
from .tasks import send_verification_email

r = redis.StrictRedis.from_url(settings.CACHES["default"]["LOCATION"])

MAX_ATTEMPTS = 3


User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        # Validate inputs
        if not username or not email or not password:
            return Response(
                {"error": "All fields are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_user = get_user_model().objects.filter(email=email).first()
        if existing_user:
            if existing_user.is_active:
                return Response(
                    {"error": "Email already exists and is active."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                # Update the inactive user's information for re-registration.
                existing_user.username = username
                existing_user.set_password(password)
                verification_code = get_random_string(
                    length=8, allowed_chars="0123456789"
                )
                existing_user.verification_code = verification_code
                existing_user.is_active = False  # remain inactive until verified
                try:
                    existing_user.save()
                except IntegrityError as e:
                    return Response(
                        {
                            "error": f"An error occurred while updating the account: {e}."
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
                # Send verification email for updated account.
                send_verification_email.delay(email, verification_code)
                return Response(
                    {
                        "message": "Registration successful. Please check your email for verification."
                    },
                    status=status.HTTP_201_CREATED,
                )
        else:
            # Create a new user if the email is not found at all.
            try:
                user = User(username=username, email=email)
                user.set_password(password)
                verification_code = get_random_string(
                    length=8, allowed_chars="0123456789"
                )
                user.verification_code = verification_code
                user.is_active = False
                user.save()
            except IntegrityError as e:
                if "duplicate key value violates unique constraint" in str(e):
                    return Response(
                        {"error": "A user with this email already exists."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                return Response(
                    {"error": "An error occurred while creating the account."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            send_verification_email.delay(email, verification_code)
            return Response(
                {
                    "message": "Registration successful. Please check your email for verification."
                },
                status=status.HTTP_201_CREATED,
            )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        username = request.data.get("username")
        verification_code = request.data.get("verification_code")

        if not email or not verification_code:
            return Response(
                {"error": "Email and verification code are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attempt_key = f"failed_attempts:{email}:{username}"
        failed_attempts = r.get(attempt_key)
        last_failed_time_key = f"last_failed_time:{email}:{username}"

        if failed_attempts and int(failed_attempts) >= MAX_ATTEMPTS:
            new_verification_code = get_random_string(
                length=8, allowed_chars="0123456789"
            )
            user = (
                get_user_model().objects.filter(email=email, username=username).first()
            )
            if user:
                user.verification_code = new_verification_code
                user.save()
                send_verification_email.delay(email, verification_code)
            time_left = timedelta(seconds=int(r.ttl(attempt_key)))
            return Response(
                {
                    "error": f"Too many failed attempts. Please try again in {time_left}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        users = get_user_model().objects.filter(email=email, username=username)

        if users.count() > 1:
            return Response(
                {"error": "Multiple users found with this email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if users.exists():
            user = users.first()

            if user.verification_code != verification_code:
                r.incr(attempt_key)

                r.expire(attempt_key, 3600)

                r.set(last_failed_time_key, timezone.now().timestamp())

                return Response(
                    {"error": "Invalid verification code."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            r.delete(attempt_key)
            r.delete(last_failed_time_key)

            user.is_active = True
            user.save()

            try:
                Profile.objects.get(user=user)
            except ObjectDoesNotExist:
                Profile.objects.create(user=user)

            return Response(
                {"message": "Email verified successfully. You can now log in."},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# User Login
class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
        )


# User Profile API


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = Profile.objects.filter(user=user).first()
        resumes = Resume.objects.filter(user=user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "profile": (
                    ProfileSerializer(profile, context={"request": request}).data
                    if profile
                    else {}
                ),
                "resumes": ResumeSerializer(resumes, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        profile = request.user.profile
        profile.bio = request.data.get("bio", profile.bio)
        profile.country = request.data.get("country", profile.country)
        profile.governorate = request.data.get("governorate", profile.governorate)

        if "profile_picture" in request.FILES:
            image_file = request.FILES["profile_picture"]
            image_type = imghdr.what(image_file)

            if image_type not in ["jpeg", "png", "gif", "bmp", "tiff", "webp"]:
                return Response({"error": "Only image files are allowed."}, status=400)

            profile.profile_picture = image_file

        profile.save()

        return Response(
            {
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "email": request.user.email,
                },
                "profile": ProfileSerializer(profile).data,
            }
        )


# Logout
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response(
                {"message": "Successfully logged out."}, status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"error": "Something went wrong."}, status=status.HTTP_400_BAD_REQUEST
            )


# Password Reset
class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return JsonResponse(
                {"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return JsonResponse(
                {"error": "User with this email does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate password reset token and UID
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(str(user.pk).encode("utf-8"))

        reset_url = f"http://localhost:3000/reset-password/{uid}/{token}/"

        # Send the reset link to the user's email
        send_mail(
            "Password Reset Request",
            f"To reset your password, please click the following link: {reset_url}",
            "from@example.com",
            [user.email],
            fail_silently=False,
        )

        return JsonResponse(
            {"message": "Password reset email sent successfully."},
            status=status.HTTP_200_OK,
        )


# Password Reset Confirm
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode("utf-8")
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return JsonResponse(
                {"error": "Invalid token or user."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return JsonResponse(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = request.data.get("password")
        if not new_password:
            return JsonResponse(
                {"error": "Password is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Update user's password and maintain session
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(
            request, user
        )  # Keep the user logged in after password change

        return JsonResponse(
            {"message": "Password reset successfully."}, status=status.HTTP_200_OK
        )
