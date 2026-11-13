# CampusConnect

CampusConnect is a Django full-stack application with server-rendered templates,
student and admin dashboards, and a PostgreSQL database.

## Local setup

1. Install Python and PostgreSQL.
2. Create and activate a virtual environment, then install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set a private Django secret key and your
   PostgreSQL connection values. `.env` is ignored by Git and must not be
   committed. For Supabase, set `DB_SSLMODE=require`.
4. Create the PostgreSQL database named in `DB_NAME`, then run:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

   Open `http://127.0.0.1:8000/`. Registration creates student accounts.
   To grant the admin dashboard role to a user, update that user's role in
   Django admin.

## Account feature

Users can register, log in and out, access their role-specific dashboard, and
view or update their own profile. Django's built-in authentication hashes
passwords. The account model enforces case-insensitive uniqueness for non-empty
email addresses.
