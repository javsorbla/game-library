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
        # login view should set a CSRF token cookie
        self.assertIn('csrftoken', response.cookies)
        # Django should also set a sessionid
        self.assertIn('sessionid', response.cookies)

        # subsequent requests should have a session key in the client
        self.assertTrue(self.client.session.session_key)

        # logout clears the session
        response = self.client.post(reverse('user-logout'))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(self.client.session.session_key)

    def test_registration_sets_csrf(self):
        # create a new user via the API (CSRF-exempt view)
        response = self.client.post(
            reverse('user-register'),
            {'username': 'bob', 'email': 'bob@example.com', 'password': 'pw'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('csrftoken', response.cookies)
        # user should exist now
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.assertTrue(User.objects.filter(username='bob').exists())
