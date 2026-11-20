from django.contrib import admin

from .models import BugDetail, Milestone, Project, ReproductionStep, Task


admin.site.register((Project, Task, Milestone, BugDetail, ReproductionStep))
