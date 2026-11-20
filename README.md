# TaskCraft

TaskCraft is a lightweight Django and PostgreSQL sprint and bug manager for
indie game developers and students building solo or small game projects. It
organizes work around game-development logic rather than general-purpose task
management.

## Features

- Private developer accounts with registration, login, logout, and profiles.
- Project creation and management.
- A four-track sprint board: Game Loop, UI/UX, State Logic, and Active Bugs.
- Task search and filtering by logic track and status.
- Milestone management and a project progress report.
- Bug reports with priority, error logs, and ordered reproduction steps.
- Owner-scoped project data; one account cannot view or change another
  developer's projects.

The application data model has seven related tables: users, projects, logic
tracks, tasks, milestones, bug details, and reproduction steps. The logic-track
table is populated with the four built-in tracks by a data migration.

## Local setup

1. Install Python and create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env`. Set a private Django secret key and your
   PostgreSQL connection values. For Supabase, use the direct or session pooler
   connection details from the Supabase dashboard and set `DB_SSLMODE=require`.
   Never commit `.env`.

3. Apply migrations and create an account:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. Start the development server and open `http://127.0.0.1:8080/`:

   ```powershell
   python manage.py runserver 127.0.0.1:8080
   ```

Run tests using the isolated SQLite test settings so the test runner does not
create a test database on your configured PostgreSQL service:

```powershell
python manage.py test accounts dashboard --settings=campusconnect.test_settings
```

## Data ownership and bug logging

Projects belong to their creator. Tasks and milestones are attached to a
project; bug details belong to an Active Bugs task and require a priority, an
error log, and at least one reproduction step. Deleting a project removes its
tasks, milestones, and associated bug reports.
