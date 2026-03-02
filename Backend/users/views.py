from rest_framework import generics, permissions

from .serializers import RegisterUserSerializer


class RegisterUserView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterUserSerializer
