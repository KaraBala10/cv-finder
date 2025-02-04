from django.contrib.auth import authenticate
from django.contrib.auth.models import User
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
        token, created = Token.objects.get_or_create(user=user)
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
            token, created = Token.objects.get_or_create(user=user)
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

        user_data = UserSerializer(user).data
        profile_data = ProfileSerializer(profile).data if profile else {}
        resume_data = ResumeSerializer(resumes, many=True).data

        return Response(
            {
                "user": user_data,
                "profile": profile_data,
                "resumes": resume_data,
            },
            status=200,
        )


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        profile, created = Profile.objects.get_or_create(user=user)

        user.username = request.data.get("username", user.username)
        user.email = request.data.get("email", user.email)
        profile.bio = request.data.get("bio", profile.bio)
        profile.location = request.data.get("location", profile.location)

        user.save()
        profile.save()

        return Response(
            {"message": "Profile updated successfully"}, status=status.HTTP_200_OK
        )

    def patch(self, request):
        return self.put(request)


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
