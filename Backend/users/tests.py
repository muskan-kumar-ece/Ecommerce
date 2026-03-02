from django.contrib.auth import get_user_model
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Coupon

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


class ReferralSummaryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="owner@example.com",
            password="StrongPass123",
            name="Owner",
        )
        self.client.force_authenticate(user=self.user)

    def test_referral_summary_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/users/referral-summary/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_referral_summary_returns_counts_rewards_and_codes(self):
        referred_success = get_user_model().objects.create_user(
            email="success@example.com",
            password="StrongPass123",
            name="Success",
        )
        referred_pending = get_user_model().objects.create_user(
            email="pending@example.com",
            password="StrongPass123",
            name="Pending",
        )
        Referral.objects.create(referrer=self.user, referred_user=referred_success, reward_issued=True)
        Referral.objects.create(referrer=self.user, referred_user=referred_pending, reward_issued=False)

        now = timezone.now()
        Coupon.objects.create(
            code="REFABCD123456",
            discount_type=Coupon.DiscountType.FIXED,
            discount_value=Decimal("100.00"),
            max_uses=1,
            per_user_limit=1,
            eligible_user=self.user,
            valid_from=now,
            valid_until=now,
            is_active=True,
        )

        response = self.client.get("/api/v1/users/referral-summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["referral_code"], self.user.referral_owner_code)
        self.assertEqual(response.data["total_referrals"], 2)
        self.assertEqual(response.data["successful_referrals"], 1)
        self.assertEqual(response.data["pending_rewards"], 1)
        self.assertEqual(response.data["earned_rewards"], "100.00")
        self.assertEqual(response.data["reward_coupon_codes"], ["REFABCD123456"])
        self.assertIn("/register/?ref=", response.data["referral_link"])
