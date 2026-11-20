from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import BugDetail, LogicTrack, Milestone, Project, ReproductionStep, Task


User = get_user_model()


class TaskCraftWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="developer",
            password="test-password",
        )
        self.other_user = User.objects.create_user(
            username="other-developer",
            password="test-password",
        )
        self.project = Project.objects.create(owner=self.user, name="Pixel Quest")
        self.loop_track = LogicTrack.objects.get(slug="game-loop")
        self.bug_track = LogicTrack.objects.get(slug="active-bugs")
        self.client.force_login(self.user)

    def test_project_crud_and_owner_isolation(self):
        response = self.client.post(
            reverse("project_create"),
            {
                "name": "Tiny Dungeon",
                "description": "A weekend prototype",
                "status": Project.Status.ACTIVE,
            },
        )
        project = Project.objects.get(name="Tiny Dungeon")
        self.assertRedirects(response, reverse("project_detail", args=[project.pk]))
        self.assertEqual(project.owner, self.user)

        response = self.client.post(
            reverse("project_update", args=[project.pk]),
            {
                "name": "Tiny Dungeon Redux",
                "description": "A weekend prototype",
                "status": Project.Status.ACTIVE,
            },
        )
        self.assertRedirects(response, reverse("project_detail", args=[project.pk]))
        project.refresh_from_db()
        self.assertEqual(project.name, "Tiny Dungeon Redux")

        self.client.force_login(self.other_user)
        self.assertEqual(
            self.client.get(reverse("project_detail", args=[project.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(reverse("project_update", args=[project.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse("project_delete", args=[project.pk])).status_code,
            404,
        )

        self.client.force_login(self.user)
        response = self.client.post(reverse("project_delete", args=[project.pk]))
        self.assertRedirects(response, reverse("dashboard"))
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

    def test_board_search_and_status_filter_are_project_scoped(self):
        matching = Task.objects.create(
            project=self.project,
            logic_track=self.loop_track,
            title="Fix jump arc",
            status=Task.Status.IN_PROGRESS,
        )
        Task.objects.create(
            project=self.project,
            logic_track=self.loop_track,
            title="Add menu music",
            status=Task.Status.TODO,
        )
        other_project = Project.objects.create(
            owner=self.user,
            name="Other Game",
        )
        Task.objects.create(
            project=other_project,
            logic_track=self.loop_track,
            title="Fix jump arc elsewhere",
            status=Task.Status.IN_PROGRESS,
        )

        response = self.client.get(
            reverse("project_detail", args=[self.project.pk]),
            {"q": "jump", "status": Task.Status.IN_PROGRESS},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, matching.title)
        self.assertNotContains(response, "Add menu music")
        self.assertNotContains(response, "Fix jump arc elsewhere")

    def test_task_cannot_reference_another_projects_milestone(self):
        second_project = Project.objects.create(
            owner=self.user,
            name="Second Game",
        )
        milestone = Milestone.objects.create(
            project=second_project,
            name="First playable",
        )

        response = self.client.post(
            reverse("task_create"),
            {
                "project": self.project.pk,
                "logic_track": self.loop_track.pk,
                "milestone": milestone.pk,
                "title": "Build prototype",
                "status": Task.Status.TODO,
                "description": "",
                "due_date": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose a milestone from this project.")
        self.assertFalse(Task.objects.filter(title="Build prototype").exists())

    def test_milestone_with_tasks_cannot_be_moved_between_projects(self):
        milestone = Milestone.objects.create(
            project=self.project,
            name="First playable",
        )
        Task.objects.create(
            project=self.project,
            logic_track=self.loop_track,
            milestone=milestone,
            title="Build core loop",
        )
        other_project = Project.objects.create(
            owner=self.user,
            name="Second Game",
        )

        response = self.client.post(
            reverse("milestone_update", args=[milestone.pk]),
            {
                "project": other_project.pk,
                "name": milestone.name,
                "description": "",
                "target_date": "",
                "status": Milestone.Status.UPCOMING,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "A milestone with assigned tasks cannot be moved to another project.",
        )
        milestone.refresh_from_db()
        self.assertEqual(milestone.project_id, self.project.pk)

    def test_bug_details_require_active_bug_task_and_save_ordered_steps(self):
        bug_task = Task.objects.create(
            project=self.project,
            logic_track=self.bug_track,
            title="Player falls through platform",
        )
        response = self.client.post(
            reverse("bug_create", args=[bug_task.pk]),
            {
                "priority": BugDetail.Priority.HIGH,
                "error_log": "NullReferenceException at PlayerController",
                "reproduction_steps": "Load level 2\nJump near the edge\n",
            },
        )

        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))
        bug = BugDetail.objects.get(task=bug_task)
        self.assertEqual(
            list(
                bug.reproduction_steps.values_list("number", "instruction")
            ),
            [(1, "Load level 2"), (2, "Jump near the edge")],
        )

        response = self.client.post(
            reverse("bug_update", args=[bug.pk]),
            {
                "priority": BugDetail.Priority.CRITICAL,
                "error_log": "Crash on respawn",
                "reproduction_steps": "Start game\nLose a life\nRespawn",
            },
        )
        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))
        bug.refresh_from_db()
        self.assertEqual(bug.priority, BugDetail.Priority.CRITICAL)
        self.assertEqual(bug.reproduction_steps.count(), 3)

        regular_task = Task.objects.create(
            project=self.project,
            logic_track=self.loop_track,
            title="Tune player movement",
        )
        self.assertEqual(
            self.client.get(reverse("bug_create", args=[regular_task.pk])).status_code,
            404,
        )
        response = self.client.post(reverse("bug_delete", args=[bug.pk]))
        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))
        self.assertFalse(BugDetail.objects.filter(pk=bug.pk).exists())

    def test_task_and_milestone_crud(self):
        response = self.client.post(
            reverse("milestone_create"),
            {
                "project": self.project.pk,
                "name": "First playable",
                "description": "A complete gameplay loop",
                "target_date": "",
                "status": Milestone.Status.UPCOMING,
            },
        )
        milestone = Milestone.objects.get(name="First playable")
        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))

        response = self.client.post(
            reverse("task_create"),
            {
                "project": self.project.pk,
                "logic_track": self.loop_track.pk,
                "milestone": milestone.pk,
                "title": "Implement player jump",
                "description": "Tune jump height",
                "status": Task.Status.TODO,
                "due_date": "",
            },
        )
        task = Task.objects.get(title="Implement player jump")
        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))

        response = self.client.post(
            reverse("task_update", args=[task.pk]),
            {
                "project": self.project.pk,
                "logic_track": self.loop_track.pk,
                "milestone": milestone.pk,
                "title": "Tune player jump",
                "description": "Tune jump height and gravity",
                "status": Task.Status.IN_PROGRESS,
                "due_date": "",
            },
        )
        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))
        task.refresh_from_db()
        self.assertEqual(task.title, "Tune player jump")
        self.assertEqual(task.status, Task.Status.IN_PROGRESS)

        response = self.client.post(reverse("task_delete", args=[task.pk]))
        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

        response = self.client.post(
            reverse("milestone_update", args=[milestone.pk]),
            {
                "project": self.project.pk,
                "name": "Vertical slice",
                "description": "First complete level",
                "target_date": "",
                "status": Milestone.Status.IN_PROGRESS,
            },
        )
        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))
        milestone.refresh_from_db()
        self.assertEqual(milestone.name, "Vertical slice")

        response = self.client.post(
            reverse("milestone_delete", args=[milestone.pk])
        )
        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))
        self.assertFalse(Milestone.objects.filter(pk=milestone.pk).exists())

    def test_report_summarizes_tasks_and_bug_priorities(self):
        Task.objects.create(
            project=self.project,
            logic_track=self.loop_track,
            title="Add camera follow",
            status=Task.Status.DONE,
        )
        bug_task = Task.objects.create(
            project=self.project,
            logic_track=self.bug_track,
            title="Game freezes after pause",
        )
        bug = BugDetail.objects.create(
            task=bug_task,
            priority=BugDetail.Priority.CRITICAL,
            error_log="Frozen update loop",
        )
        ReproductionStep.objects.create(
            bug_detail=bug,
            number=1,
            instruction="Pause while transitioning scenes",
        )
        Milestone.objects.create(project=self.project, name="Vertical slice")

        response = self.client.get(reverse("project_report", args=[self.project.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_tasks"], 2)
        self.assertEqual(response.context["completed_tasks"], 1)
        self.assertEqual(response.context["bug_count"], 1)
        self.assertContains(response, "Critical")

    def test_user_cannot_edit_or_delete_another_users_task(self):
        task = Task.objects.create(
            project=self.project,
            logic_track=self.loop_track,
            title="Private task",
        )
        self.client.force_login(self.other_user)

        self.assertEqual(
            self.client.get(reverse("task_update", args=[task.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse("task_delete", args=[task.pk])).status_code,
            404,
        )
