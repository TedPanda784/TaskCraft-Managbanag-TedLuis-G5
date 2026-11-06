from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser


class CampusConnectAdminPanelTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            username="siteadmin",
            email="admin@example.com",
            password="test-password",
        )

    def test_superuser_can_open_panel_with_student_role(self):
        self.assertEqual(self.admin.role, CustomUser.Role.STUDENT)
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin_panel"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Panel")
        self.assertContains(response, "Total members")

    def test_superuser_sees_panel_link_on_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, reverse("admin_panel"))

    def test_admin_role_can_open_panel(self):
        admin = CustomUser.objects.create_user(
            username="campusadmin",
            password="test-password",
            role=CustomUser.Role.ADMIN,
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("admin_panel"))

        self.assertEqual(response.status_code, 200)

    def test_student_cannot_open_panel(self):
        student = CustomUser.objects.create_user(
            username="student",
            password="test-password",
        )
        self.client.force_login(student)

        response = self.client.get(reverse("admin_panel"))

        self.assertEqual(response.status_code, 403)
