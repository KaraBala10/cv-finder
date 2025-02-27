import imghdr
from datetime import timedelta

import redis
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
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


class PublicUserProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username, *args, **kwargs):
        user = get_object_or_404(User, username=username)
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

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(str(user.pk).encode("utf-8"))

        reset_url = f"http://localhost:3000/reset-password/{uid}/{token}/"

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

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return JsonResponse(
            {"message": "Password reset successfully."}, status=status.HTTP_200_OK
        )


class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        title = request.data.get("title")
        file = request.FILES.get("file")

        if not title or not file:
            return Response(
                {"error": "Both title and file are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Resume.objects.filter(user=user).exists():
            return Response(
                {"error": "You can only upload one resume."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "." not in file.name:
            return Response(
                {"error": "Your file does not have an extension."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ext = file.name.split(".")[-1]
        file.name = f"{title}.{ext}"

        resume = Resume(user=user, title=title, file=file)
        resume.save()

        return Response(
            {"message": "Resume uploaded successfully."},
            status=status.HTTP_201_CREATED,
        )


class ResumeDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        resume_id = kwargs.get("resume_id")
        user = request.user

        try:
            resume = Resume.objects.get(id=resume_id, user=user)
            resume.delete()
            return Response(
                {"message": "Resume deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Resume.DoesNotExist:
            return Response(
                {"error": "Resume not found."}, status=status.HTTP_404_NOT_FOUND
            )


class ResumeViewPDF(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username, *args, **kwargs):
        user = get_object_or_404(User, username=username)
        resume = get_object_or_404(Resume, user=user)
        if not resume.file.name.lower().endswith(".pdf"):
            raise Http404("Resume is not a PDF file.")
        expected_suffix = f"{user.username}_resume.pdf"
        if not resume.file.name.endswith(expected_suffix):
            pass
        try:
            return FileResponse(
                open(resume.file.path, "rb"), content_type="application/pdf"
            )
        except FileNotFoundError:
            raise Http404("Resume file not found.")


class ResumeDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username, *args, **kwargs):
        # Get the user by username
        user = get_object_or_404(User, username=username)
        # Get the resume associated with the user
        resume = get_object_or_404(Resume, user=user)

        # Ensure the file is a PDF (optional)
        if not resume.file.name.lower().endswith(".pdf"):
            raise Http404("Resume is not a PDF file.")

        try:
            # Open the file and create a FileResponse
            response = FileResponse(
                open(resume.file.path, "rb"), content_type="application/pdf"
            )
            # Set Content-Disposition header to force download with a specific filename
            response["Content-Disposition"] = (
                f'attachment; filename="{user.username}_resume.pdf"'
            )
            return response
        except FileNotFoundError:
            raise Http404("Resume file not found.")
