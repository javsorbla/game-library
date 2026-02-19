from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import UserSerializer


@method_decorator(csrf_exempt, name='dispatch')
class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # ensure CSRF token is available for subsequent requests
        response.set_cookie('csrftoken', get_token(request))
        return response


from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            response = Response({'username': user.username}, status=status.HTTP_200_OK)
            response.set_cookie('csrftoken', get_token(request))
            return response
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    # allow logout without CSRF; response will clear the cookie so the
    # browser no longer sends an (invalid) sessionid.
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # even if the user is anonymous, calling logout is harmless
        logout(request)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        # instruct browser to delete the sessionid cookie
        response.delete_cookie('sessionid', path='/')
        return response
