from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import CustomUser


User = get_user_model()


class AccountFlowTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="A-very-strong-Password-938!",
            first_name="Sam",
            role=CustomUser.Role.STUDENT,
        )

    def test_registration_creates_hashed_student_account_and_message(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newstudent",
                "email": "NewStudent@example.com",
                "first_name": "New",
                "last_name": "Student",
                "role": CustomUser.Role.ADMIN,
                "course": "Computing",
                "phone_number": "555-0123",
                "password1": "A-different-Strong-Password-938!",
                "password2": "A-different-Strong-Password-938!",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="newstudent")
        self.assertEqual(user.email, "newstudent@example.com")
        self.assertEqual(user.role, CustomUser.Role.STUDENT)
        self.assertTrue(user.check_password("A-different-Strong-Password-938!"))
        self.assertNotEqual(user.password, "A-different-Strong-Password-938!")
        self.assertContains(response, "Your account was created")

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "anotherstudent",
                "email": "STUDENT@example.com",
                "password1": "A-different-Strong-Password-938!",
                "password2": "A-different-Strong-Password-938!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email already exists.")
        self.assertFalse(User.objects.filter(username="anotherstudent").exists())

    def test_registration_rejects_invalid_email_and_missing_required_fields(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "bademail",
                "email": "not-an-email",
                "password1": "A-different-Strong-Password-938!",
                "password2": "A-different-Strong-Password-938!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address.")
        self.assertFalse(User.objects.filter(username="bademail").exists())

        response = self.client.post(reverse("signup"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_registration_requires_matching_passwords(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "mismatch",
                "email": "mismatch@example.com",
                "password1": "A-different-Strong-Password-938!",
                "password2": "A-different-Strong-Password-939!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two password fields didn’t match.")
        self.assertFalse(User.objects.filter(username="mismatch").exists())

    def test_login_rejects_invalid_credentials_and_redirects_valid_user(self):
        response = self.client.post(
            reverse("login"),
            {"username": "student", "password": "incorrect"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password.")

        response = self.client.post(
            reverse("login"),
            {"username": "student", "password": "A-very-strong-Password-938!"},
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.student.pk)

    def test_logout_ends_session(self):
        self.client.force_login(self.student)

        response = self.client.post(reverse("logout"), follow=True)

        self.assertRedirects(response, reverse("login"))
        self.assertContains(response, "You have been logged out.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_does_not_accept_get(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_logged_out_user_is_redirected_from_dashboard_and_profile(self):
        for url in (reverse("dashboard"), reverse("profile")):
            response = self.client.get(url)
            self.assertRedirects(
                response,
                f"{reverse('login')}?next={url}",
            )

    def test_dashboard_uses_taskcraft_branding(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "TaskCraft")
        self.assertContains(response, "game-loop tasks")

    def test_profile_update_changes_only_the_signed_in_user(self):
        other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="A-very-strong-Password-938!",
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("profile"),
            {
                "first_name": "Updated",
                "last_name": "Name",
                "email": "UPDATED@example.com",
            },
        )

        self.assertRedirects(response, reverse("profile"))
        self.student.refresh_from_db()
        other_user.refresh_from_db()
        self.assertEqual(self.student.first_name, "Updated")
        self.assertEqual(self.student.email, "updated@example.com")
        self.assertEqual(other_user.email, "other@example.com")

    def test_profile_rejects_another_users_email(self):
        User.objects.create_user(
            username="other",
            email="other@example.com",
            password="A-very-strong-Password-938!",
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("profile"),
            {
                "first_name": "Sam",
                "last_name": "",
                "email": "OTHER@example.com",
                "course": "",
                "phone_number": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email already exists.")
