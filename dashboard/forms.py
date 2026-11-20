from django import forms

from .models import BugDetail, LogicTrack, Milestone, Project, ReproductionStep, Task


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "status")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = (
            "project",
            "logic_track",
            "milestone",
            "title",
            "description",
            "status",
            "due_date",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        projects = Project.objects.filter(owner=user)
        self.fields["project"].queryset = projects
        self.fields["milestone"].queryset = Milestone.objects.filter(
            project__owner=user
        )
        self.fields["milestone"].required = False
        self.fields["milestone"].empty_label = "No milestone"
        self.fields["logic_track"].queryset = LogicTrack.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get("project")
        milestone = cleaned_data.get("milestone")
        if project and milestone and milestone.project_id != project.pk:
            self.add_error("milestone", "Choose a milestone from this project.")
        return cleaned_data


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ("project", "name", "description", "target_date", "status")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "target_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.filter(owner=user)

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get("project")
        if (
            self.instance.pk
            and project
            and project.pk != self.instance.project_id
            and self.instance.tasks.exists()
        ):
            self.add_error(
                "project",
                "A milestone with assigned tasks cannot be moved to another project.",
            )
        return cleaned_data


class BugDetailForm(forms.ModelForm):
    reproduction_steps = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text="Enter one reproduction step per line.",
    )

    class Meta:
        model = BugDetail
        fields = ("priority", "error_log")
        widgets = {
            "error_log": forms.Textarea(attrs={"rows": 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["reproduction_steps"] = "\n".join(
                self.instance.reproduction_steps.values_list(
                    "instruction", flat=True
                )
            )

    def clean_reproduction_steps(self):
        steps = [
            line.strip()
            for line in self.cleaned_data["reproduction_steps"].splitlines()
            if line.strip()
        ]
        if not steps:
            raise forms.ValidationError("Add at least one reproduction step.")
        return steps

    def save(self, commit=True):
        bug_detail = super().save(commit=False)
        if commit:
            bug_detail.save()
            self.save_m2m()
            ReproductionStep.objects.filter(bug_detail=bug_detail).delete()
            ReproductionStep.objects.bulk_create(
                ReproductionStep(
                    bug_detail=bug_detail,
                    number=number,
                    instruction=instruction,
                )
                for number, instruction in enumerate(
                    self.cleaned_data["reproduction_steps"], start=1
                )
            )
        return bug_detail
