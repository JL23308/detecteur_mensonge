from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from api.models import Device, Session

class AuthTests(APITestCase):
    def test_register_user(self):
        url = '/api/users/register/'
        data = {'username': 'newuser', 'password': 'password123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('token' in response.data)

    def test_login_user(self):
        User.objects.create_user(username="testuser", password="password")
        url = '/api/users/login/'
        data = {'username': 'testuser', 'password': 'password'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.data)

class DeviceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.login(username='testuser', password='password')
        # DRF needs the token to force authenticate sometimes
        response = self.client.post('/api/users/login/', {'username': 'testuser', 'password': 'password'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['token'])

    def test_create_device(self):
        url = '/api/devices/'
        data = {'mac_address': '00:11:22:33:44', 'name': 'My Device'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.count(), 1)
        self.assertEqual(Device.objects.get().user, self.user)
