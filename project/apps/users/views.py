from drf_util.decorators import serialize_decorator
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import IntegrityError

from .serializers import UserSerializer
from .models import CustomUser


class RegisterUserView(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    @serialize_decorator(UserSerializer)
    def post(self, request):
        validated_data = request.serializer.validated_data

        try:
            user = CustomUser.objects.create(
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                email=validated_data['email'],
                is_superuser=True,
                is_staff=True
            )
            user.set_password(validated_data['password'])
            user.save()
        except IntegrityError:
            return Response({'detail': 'email must be unique'})

        refresh = RefreshToken.for_user(user)
        token_data = {
            'refresh_token': str(refresh),
            'access_token': str(refresh.access_token),
        }

        return Response(token_data, status=status.HTTP_201_CREATED)


class ListUserView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
