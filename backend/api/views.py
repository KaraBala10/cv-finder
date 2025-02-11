from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile, Resume
from .serializers import ProfileSerializer, ResumeSerializer, UserSerializer


# User Registration (Sign Up)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
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
                "profile": ProfileSerializer(profile).data if profile else {},
                "resumes": ResumeSerializer(resumes, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


# Profile Update
class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def update_user_and_profile(self, user, profile, data):
        user.username = data.get("username", user.username)
        user.email = data.get("email", user.email)
        profile.bio = data.get("bio", profile.bio)
        profile.location = data.get("location", profile.location)

        user.save()
        profile.save()

    def put(self, request):
        user = request.user
        profile, _ = Profile.objects.get_or_create(user=user)

        self.update_user_and_profile(user, profile, request.data)

        return Response(
            {"message": "Profile updated successfully"}, status=status.HTTP_200_OK
        )

    def patch(self, request):
        return self.put(request)


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
            user = User.objects.get(email=email)
        except User.DoesNotExist:
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
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
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
