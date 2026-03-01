from django.contrib.auth import get_user_model
from django.test import TestCase


class UserModelTests(TestCase):
    def test_create_user_with_email(self):
        user = get_user_model().objects.create_user(
            email="student@example.com",
            password="secure-pass-123",
            full_name="Student User",
        )

        self.assertEqual(user.email, "student@example.com")
        self.assertEqual(user.role, "STUDENT")
        self.assertTrue(user.check_password("secure-pass-123"))

    def test_create_superuser_sets_admin_role(self):
        superuser = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="secure-pass-123",
            full_name="Admin User",
        )

        self.assertEqual(superuser.role, "ADMIN")
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
