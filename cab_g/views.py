from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.contrib.auth.models import User
from .serializers import RegisterSerializer,DoctorSerializer
from .models import Doctor
from rest_framework import generics

# Create your views here.

class HelloView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        content = {'message': 'Hello, World!', "user": request.user.username}
        return Response(content)


class CreateDoctorView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = DoctorSerializer
    # authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    

# user registrations
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer