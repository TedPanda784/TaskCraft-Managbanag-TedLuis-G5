from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
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

from accounts.models import CustomUser

from .forms import BugDetailForm, MilestoneForm, ProjectForm, TaskForm
from .models import BugDetail, LogicTrack, Milestone, Project, Task


def _admin_dashboard_context():
    return {
        "member_count": CustomUser.objects.count(),
        "student_count": CustomUser.objects.filter(
            role=CustomUser.Role.STUDENT
        ).count(),
        "admin_count": CustomUser.objects.filter(
            role=CustomUser.Role.ADMIN
        ).count(),
        "recent_members": CustomUser.objects.order_by("-date_joined")[:10],
    }


class AdminRoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.role == CustomUser.Role.ADMIN


class PostOnlyUpdateView(UpdateView):
    http_method_names = ["get", "post", "head", "options"]


class PostOnlyDeleteView(DeleteView):
    http_method_names = ["get", "post", "head", "options"]


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def is_admin(self):
        user = self.request.user
        return user.is_superuser or user.role == CustomUser.Role.ADMIN

    def get_template_names(self):
        if self.is_admin():
            return ["dashboard/admin_panel.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_admin():
            context.update(_admin_dashboard_context())
            return context

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


class AdminPanelView(AdminRoleRequiredMixin, TemplateView):
    template_name = "dashboard/admin_panel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_admin_dashboard_context())
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


class ProjectCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Create a project"}
    success_message = "Project created successfully."

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.pk})


class OwnedProjectMixin:
    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)


class ProjectUpdateView(
    LoginRequiredMixin, SuccessMessageMixin, OwnedProjectMixin, PostOnlyUpdateView
):
    model = Project
    form_class = ProjectForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Edit project"}
    success_message = "Project updated successfully."

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.pk})


class DeleteSuccessMessageMixin:
    success_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class ProjectDeleteView(
    LoginRequiredMixin,
    DeleteSuccessMessageMixin,
    OwnedProjectMixin,
    PostOnlyDeleteView,
):
    model = Project
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard")
    extra_context = {"page_title": "Delete project"}
    success_message = "Project deleted successfully."


class UserFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class TaskCreateView(
    LoginRequiredMixin, UserFormMixin, SuccessMessageMixin, CreateView
):
    model = Task
    form_class = TaskForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Add a task"}
    success_message = "Task created successfully."

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


class TaskUpdateView(
    LoginRequiredMixin,
    UserFormMixin,
    SuccessMessageMixin,
    OwnedTaskMixin,
    PostOnlyUpdateView,
):
    model = Task
    form_class = TaskForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Edit task"}
    success_message = "Task updated successfully."

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.project_id})


class TaskDeleteView(
    LoginRequiredMixin, DeleteSuccessMessageMixin, OwnedTaskMixin, PostOnlyDeleteView
):
    model = Task
    template_name = "dashboard/confirm_delete.html"
    extra_context = {"page_title": "Delete task"}
    success_message = "Task deleted successfully."

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.project_id})


class MilestoneCreateView(
    LoginRequiredMixin, UserFormMixin, SuccessMessageMixin, CreateView
):
    model = Milestone
    form_class = MilestoneForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Add a milestone"}
    success_message = "Milestone created successfully."

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
    LoginRequiredMixin,
    UserFormMixin,
    SuccessMessageMixin,
    OwnedMilestoneMixin,
    PostOnlyUpdateView,
):
    model = Milestone
    form_class = MilestoneForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Edit milestone"}
    success_message = "Milestone updated successfully."

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.project_id})


class MilestoneDeleteView(
    LoginRequiredMixin,
    DeleteSuccessMessageMixin,
    OwnedMilestoneMixin,
    PostOnlyDeleteView,
):
    model = Milestone
    template_name = "dashboard/confirm_delete.html"
    extra_context = {"page_title": "Delete milestone"}
    success_message = "Milestone deleted successfully."

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.project_id})


class BugDetailCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = BugDetail
    form_class = BugDetailForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Log bug details"}
    success_message = "Bug details saved successfully."

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
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
    LoginRequiredMixin, SuccessMessageMixin, OwnedBugDetailMixin, PostOnlyUpdateView
):
    model = BugDetail
    form_class = BugDetailForm
    template_name = "dashboard/form.html"
    extra_context = {"page_title": "Edit bug details"}
    success_message = "Bug details updated successfully."

    def form_valid(self, form):
        with transaction.atomic():
            return super().form_valid(form)

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.task.project_id})


class BugDetailDeleteView(
    LoginRequiredMixin,
    DeleteSuccessMessageMixin,
    OwnedBugDetailMixin,
    PostOnlyDeleteView,
):
    model = BugDetail
    template_name = "dashboard/confirm_delete.html"
    extra_context = {"page_title": "Delete bug details"}
    success_message = "Bug details deleted successfully."

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
