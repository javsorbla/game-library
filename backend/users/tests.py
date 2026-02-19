from django.test import TestCase
from django.urls import reverse

from django.contrib.auth import get_user_model


class AuthTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="secret")

    def test_login_logout_flow(self):
        # login with valid credentials
        response = self.client.post(reverse('user-login'), {'username': 'alice', 'password': 'secret'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.data)

        # subsequent requests should have session cookie set
        resp2 = self.client.get(reverse('user-login'))
        # GET isn't implemented, but cookie should still exist
        self.assertTrue(self.client.session.session_key)

        # logout
        response = self.client.post(reverse('user-logout'))
        self.assertEqual(response.status_code, 204)
