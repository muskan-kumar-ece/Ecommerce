from django.contrib.auth import get_user_model
from django.test import TestCase


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
