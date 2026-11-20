from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    TemplateView,
    UpdateView,
)

from .forms import BugDetailForm, MilestoneForm, ProjectForm, TaskForm
from .models import BugDetail, LogicTrack, Milestone, Project, Task


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_projects = Project.objects.filter(owner=self.request.user)
        projects = user_projects.annotate(
            task_count=Count("tasks", distinct=True),
            open_task_count=Count(
                "tasks",
                filter=~Q(tasks__status=Task.Status.DONE),
                distinct=True,
            ),
            bug_count=Count("tasks__bug_detail", distinct=True),
        )
        user_tasks = Task.objects.filter(project__owner=self.request.user)
        context.update(
            projects=projects,
            project_count=user_projects.count(),
            open_task_count=user_tasks.exclude(status=Task.Status.DONE).count(),
            completed_task_count=user_tasks.filter(status=Task.Status.DONE).count(),
            open_bug_count=BugDetail.objects.filter(
                task__project__owner=self.request.user,
                task__status__in=(Task.Status.TODO, Task.Status.IN_PROGRESS),
            ).count(),
        )
        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "dashboard/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = (
            Task.objects.filter(project=self.object)
            .select_related("logic_track", "milestone", "bug_detail")
            .prefetch_related("bug_detail__reproduction_steps")
        )
        search = self.request.GET.get("q", "").strip()
        track_slug = self.request.GET.get("track", "")
        status = self.request.GET.get("status", "")
        if search:
            tasks = tasks.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        if LogicTrack.objects.filter(slug=track_slug).exists():
            tasks = tasks.filter(logic_track__slug=track_slug)
        valid_statuses = dict(Task.Status.choices)
        if status in valid_statuses:
            tasks = tasks.filter(status=status)
        context.update(
            track_sections=[
                {"track": track, "tasks": tasks.filter(logic_track=track)}
                for track in LogicTrack.objects.all()
            ],
            tracks=LogicTrack.objects.all(),
            task_statuses=Task.Status.choices,
            search=search,
            selected_track=track_slug,
            selected_status=status,
            milestones=self.object.milestones.all(),
        )
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Create a project"}

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.pk})


class OwnedProjectMixin:
    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)


class ProjectUpdateView(LoginRequiredMixin, OwnedProjectMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Edit project"}

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.pk})


class ProjectDeleteView(LoginRequiredMixin, OwnedProjectMixin, DeleteView):
    model = Project
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard")
    extra_context = {"page_title": "Delete project"}


class UserFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class TaskCreateView(LoginRequiredMixin, UserFormMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Add a task"}

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.request.GET.get("project")
        if project_id and Project.objects.filter(
            pk=project_id, owner=self.request.user
        ).exists():
            initial["project"] = project_id
        return initial

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.project_id})


class OwnedTaskMixin:
    def get_queryset(self):
        return Task.objects.filter(project__owner=self.request.user)


class TaskUpdateView(LoginRequiredMixin, UserFormMixin, OwnedTaskMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Edit task"}

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.project_id})


class TaskDeleteView(LoginRequiredMixin, OwnedTaskMixin, DeleteView):
    model = Task
    template_name = "dashboard/confirm_delete.html"
    extra_context = {"page_title": "Delete task"}

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.project_id})


class MilestoneCreateView(LoginRequiredMixin, UserFormMixin, CreateView):
    model = Milestone
    form_class = MilestoneForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Add a milestone"}

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.request.GET.get("project")
        if project_id and Project.objects.filter(
            pk=project_id, owner=self.request.user
        ).exists():
            initial["project"] = project_id
        return initial

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.project_id})


class OwnedMilestoneMixin:
    def get_queryset(self):
        return Milestone.objects.filter(project__owner=self.request.user)


class MilestoneUpdateView(
    LoginRequiredMixin, UserFormMixin, OwnedMilestoneMixin, UpdateView
):
    model = Milestone
    form_class = MilestoneForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Edit milestone"}

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.project_id})


class MilestoneDeleteView(LoginRequiredMixin, OwnedMilestoneMixin, DeleteView):
    model = Milestone
    template_name = "dashboard/confirm_delete.html"
    extra_context = {"page_title": "Delete milestone"}

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.project_id})


class BugDetailCreateView(LoginRequiredMixin, CreateView):
    model = BugDetail
    form_class = BugDetailForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Log bug details"}

    def dispatch(self, request, *args, **kwargs):
        self.task = get_object_or_404(
            Task,
            pk=kwargs["task_pk"],
            project__owner=request.user,
            logic_track__slug="active-bugs",
        )
        try:
            bug_detail = self.task.bug_detail
        except BugDetail.DoesNotExist:
            bug_detail = None
        if bug_detail:
            return redirect("bug_update", pk=bug_detail.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.task = self.task
        with transaction.atomic():
            return super().form_valid(form)

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.task.project_id})


class OwnedBugDetailMixin:
    def get_queryset(self):
        return BugDetail.objects.filter(
            task__project__owner=self.request.user,
            task__logic_track__slug="active-bugs",
        )


class BugDetailUpdateView(
    LoginRequiredMixin, OwnedBugDetailMixin, UpdateView
):
    model = BugDetail
    form_class = BugDetailForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Edit bug details"}

    def form_valid(self, form):
        with transaction.atomic():
            return super().form_valid(form)

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.task.project_id})


class BugDetailDeleteView(LoginRequiredMixin, OwnedBugDetailMixin, DeleteView):
    model = BugDetail
    template_name = "dashboard/confirm_delete.html"
    extra_context = {"page_title": "Delete bug details"}

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.task.project_id})


class ProjectReportView(ProjectDetailView):
    template_name = "dashboard/project_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = Task.objects.filter(project=self.object)
        context.update(
            total_tasks=tasks.count(),
            completed_tasks=tasks.filter(status=Task.Status.DONE).count(),
            in_progress_tasks=tasks.filter(
                status=Task.Status.IN_PROGRESS
            ).count(),
            todo_tasks=tasks.filter(status=Task.Status.TODO).count(),
            track_summary=LogicTrack.objects.annotate(
                task_count=Count("tasks", filter=Q(tasks__project=self.object)),
                completed_count=Count(
                    "tasks",
                    filter=Q(
                        tasks__project=self.object,
                        tasks__status=Task.Status.DONE,
                    ),
                ),
            ),
            bug_summary=BugDetail.objects.filter(
                task__project=self.object
            ).values("priority").annotate(total=Count("id")).order_by("priority"),
            bug_count=BugDetail.objects.filter(task__project=self.object).count(),
            milestone_count=self.object.milestones.count(),
        )
        return context
