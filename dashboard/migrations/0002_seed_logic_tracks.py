from django.db import migrations


TRACKS = (
    ("Game Loop", "game-loop", 1),
    ("UI/UX", "ui-ux", 2),
    ("State Logic", "state-logic", 3),
    ("Active Bugs", "active-bugs", 4),
)


def create_logic_tracks(apps, schema_editor):
    LogicTrack = apps.get_model("dashboard", "LogicTrack")
    LogicTrack.objects.using(schema_editor.connection.alias).bulk_create(
        [
            LogicTrack(name=name, slug=slug, position=position)
            for name, slug, position in TRACKS
        ]
    )


def remove_logic_tracks(apps, schema_editor):
    LogicTrack = apps.get_model("dashboard", "LogicTrack")
    LogicTrack.objects.using(schema_editor.connection.alias).filter(
        slug__in=[slug for _, slug, _ in TRACKS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_logic_tracks, remove_logic_tracks),
    ]
