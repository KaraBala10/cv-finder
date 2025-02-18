import imghdr

from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser  # Ensure you import your CustomUser model
from .models import Profile, Resume
from .serializers import ProfileSerializer, ResumeSerializer, UserSerializer
from .tasks import send_verification_email


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Ensure the Profile is created for the new user
        profile, _ = Profile.objects.get_or_create(user=user)

        # Generate the 8-digit verification code
        verification_code = get_random_string(length=8, allowed_chars="0123456789")

        # Store the verification code in the Profile model
        profile.verification_code = verification_code
        profile.save()

        # Send the verification code to the user's email asynchronously
        send_verification_email.delay(user.email, verification_code)

        # Create a token for the user and return the response
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user": serializer.data},
            status=status.HTTP_201_CREATED,
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
