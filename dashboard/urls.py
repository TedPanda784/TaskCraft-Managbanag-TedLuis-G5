from django.urls import path

from .views import (
    BugDetailCreateView,
    BugDetailDeleteView,
    BugDetailUpdateView,
    DashboardView,
    MilestoneCreateView,
    MilestoneDeleteView,
    MilestoneUpdateView,
    ProjectCreateView,
    ProjectDeleteView,
    ProjectDetailView,
    ProjectReportView,
    ProjectUpdateView,
    TaskCreateView,
    TaskDeleteView,
    TaskUpdateView,
    AdminPanelView,
)


urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("admin-panel/", AdminPanelView.as_view(), name="admin_panel"),
    path("projects/new/", ProjectCreateView.as_view(), name="project_create"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project_detail"),
    path(
        "projects/<int:pk>/edit/",
        ProjectUpdateView.as_view(),
        name="project_update",
    ),
    path(
        "projects/<int:pk>/delete/",
        ProjectDeleteView.as_view(),
        name="project_delete",
    ),
    path(
        "projects/<int:pk>/report/",
        ProjectReportView.as_view(),
        name="project_report",
    ),
    path("tasks/new/", TaskCreateView.as_view(), name="task_create"),
    path("tasks/<int:pk>/edit/", TaskUpdateView.as_view(), name="task_update"),
    path("tasks/<int:pk>/delete/", TaskDeleteView.as_view(), name="task_delete"),
    path("milestones/new/", MilestoneCreateView.as_view(), name="milestone_create"),
    path(
        "milestones/<int:pk>/edit/",
        MilestoneUpdateView.as_view(),
        name="milestone_update",
    ),
    path(
        "milestones/<int:pk>/delete/",
        MilestoneDeleteView.as_view(),
        name="milestone_delete",
    ),
    path(
        "tasks/<int:task_pk>/bug/",
        BugDetailCreateView.as_view(),
        name="bug_create",
    ),
    path(
        "bugs/<int:pk>/edit/",
        BugDetailUpdateView.as_view(),
        name="bug_update",
    ),
    path(
        "bugs/<int:pk>/delete/",
        BugDetailDeleteView.as_view(),
        name="bug_delete",
    ),
]
