from django.conf import settings
from django.db import models
from django.db.models import Q


class Project(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_projects",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("owner", "name"),
                name="unique_project_name_per_owner",
            ),
            models.CheckConstraint(
                condition=Q(status__in=("ACTIVE", "COMPLETED")),
                name="project_status_valid",
            ),
            models.CheckConstraint(
                condition=~Q(name=""),
                name="project_name_not_empty",
            ),
        ]

    def __str__(self):
        return self.name


class LogicTrack(models.Model):
    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=40, unique=True)
    position = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        ordering = ("position",)
        constraints = [
            models.CheckConstraint(
                condition=Q(position__gte=1, position__lte=4),
                name="logic_track_position_in_range",
            ),
            models.CheckConstraint(
                condition=Q(slug__in=("game-loop", "ui-ux", "state-logic", "active-bugs")),
                name="logic_track_slug_valid",
            ),
        ]

    def __str__(self):
        return self.name


class Milestone(models.Model):
    class Status(models.TextChoices):
        UPCOMING = "UPCOMING", "Upcoming"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETE = "COMPLETE", "Complete"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="milestones",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.UPCOMING,
    )

    class Meta:
        ordering = ("target_date", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("project", "name"),
                name="unique_milestone_name_per_project",
            ),
            models.CheckConstraint(
                condition=Q(status__in=("UPCOMING", "IN_PROGRESS", "COMPLETE")),
                name="milestone_status_valid",
            ),
            models.CheckConstraint(
                condition=~Q(name=""),
                name="milestone_name_not_empty",
            ),
        ]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "TODO", "To do"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        DONE = "DONE", "Done"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    logic_track = models.ForeignKey(
        LogicTrack,
        on_delete=models.PROTECT,
        related_name="tasks",
    )
    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.SET_NULL,
        related_name="tasks",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.TODO,
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("logic_track__position", "due_date", "title")
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=("TODO", "IN_PROGRESS", "DONE")),
                name="task_status_valid",
            ),
            models.CheckConstraint(
                condition=~Q(title=""),
                name="task_title_not_empty",
            ),
        ]

    def __str__(self):
        return self.title


class BugDetail(models.Model):
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    task = models.OneToOneField(
        Task,
        on_delete=models.CASCADE,
        related_name="bug_detail",
    )
    priority = models.CharField(max_length=10, choices=Priority.choices)
    error_log = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(error_log=""),
                name="bug_error_log_not_empty",
            ),
            models.CheckConstraint(
                condition=Q(priority__in=("LOW", "MEDIUM", "HIGH", "CRITICAL")),
                name="bug_priority_valid",
            ),
        ]

    def __str__(self):
        return f"{self.task.title} ({self.get_priority_display()})"


class ReproductionStep(models.Model):
    bug_detail = models.ForeignKey(
        BugDetail,
        on_delete=models.CASCADE,
        related_name="reproduction_steps",
    )
    number = models.PositiveSmallIntegerField()
    instruction = models.TextField()

    class Meta:
        ordering = ("number",)
        constraints = [
            models.UniqueConstraint(
                fields=("bug_detail", "number"),
                name="unique_bug_reproduction_step_number",
            ),
            models.CheckConstraint(
                condition=Q(number__gte=1),
                name="bug_reproduction_step_number_positive",
            ),
            models.CheckConstraint(
                condition=~Q(instruction=""),
                name="bug_reproduction_step_not_empty",
            ),
        ]

    def __str__(self):
        return f"Step {self.number}: {self.instruction[:60]}"
