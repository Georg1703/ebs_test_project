import json

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import CustomUser


class AccountTests(APITestCase):

    def test_register_user(self):
        url = '/users/register/'
        data = {
            'email': 'aaa.asdas@gmail.com',
            'password': '1234',
            'first_name': 'first_name',
            'last_name': 'last_name',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(CustomUser.objects.get().email, 'aaa.asdas@gmail.com')

    def test_login_user(self):
        user = CustomUser.objects.create(email='aaa.asdas@gmail.com')
        user.set_password('1234')
        user.save()

        url = '/users/login/'
        data = {
            'email': 'aaa.asdas@gmail.com',
            'password': '1234',
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
