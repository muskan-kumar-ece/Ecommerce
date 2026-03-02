from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Referral


class UserModelTests(TestCase):
    def test_create_user_with_email_as_username(self):
        user = get_user_model().objects.create_user(
            email="student@example.com",
            password="StrongPass123",
            name="Student",
        )

        self.assertEqual(user.email, "student@example.com")
        self.assertEqual(user.role, get_user_model().Role.STUDENT)
        self.assertTrue(user.check_password("StrongPass123"))

    def test_create_superuser_enforces_admin_role(self):
        admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="StrongPass123",
            name="Admin",
        )

        self.assertEqual(admin_user.role, get_user_model().Role.ADMIN)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class UserRegistrationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_user_with_referral_code_links_referral(self):
        referrer = get_user_model().objects.create_user(
            email="referrer@example.com",
            password="StrongPass123",
            name="Referrer",
        )

        response = self.client.post(
            "/api/v1/users/register/",
            {
                "name": "Referred",
                "email": "referred@example.com",
                "password": "StrongPass123",
                "referral_code": referrer.referral_owner_code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        referred_user = get_user_model().objects.get(email="referred@example.com")
        referral = Referral.objects.get(referred_user=referred_user)
        self.assertEqual(referral.referrer_id, referrer.id)

    def test_register_user_with_invalid_referral_code_fails(self):
        response = self.client.post(
            "/api/v1/users/register/",
            {
                "name": "Referred",
                "email": "invalid-code@example.com",
                "password": "StrongPass123",
                "referral_code": "INVALIDCODE",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
