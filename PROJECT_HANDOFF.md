# CameroonTechJobs Project Handoff

This file is an up-to-date handoff for another AI or developer to quickly understand the current state of the `cameroon_tech_jobs` project, what has been built, how it works, how it is deployed, and what the next priorities are.

## 1. Project Identity

- Project name: `CameroonTechJobs`
- Purpose: a focused hiring platform for Cameroon tech
- Current direction:
  - started as a tech job board
  - evolving into a hiring workflow platform
  - employers can now post jobs, receive applications, message candidates, update statuses, schedule interviews, and receive notifications
  - seekers can create profiles, apply, track applications, message employers, respond to interviews, and receive notifications

## 2. Tech Stack

- Backend: Django
- Database:
  - local: SQLite
  - production: PostgreSQL via `DATABASE_URL`
- Static files: WhiteNoise
- Image hosting:
  - seeker profile photos: Cloudinary
  - company logos: still standard Django/ImageField flow
- Email:
  - SMTP when env vars are present
  - console backend fallback locally
- Deployment: Render

## 3. Repo Structure

- `config/`
  - Django settings, urls, wsgi, asgi
- `jobs/`
  - jobs, categories, tech stacks, applications, messages, interviews, notifications
- `companies/`
  - custom company auth model and employer dashboard
- `seekers/`
  - seeker auth model, seeker profile, seeker dashboard
- `pages/`
  - homepage, about, contact, informational pages
- `templates/`
  - all UI templates
- `static/`
  - CSS, JS, images, manifest
- `build.sh`
  - Render build/migrate/seed flow

## 4. Auth Model Design

This project uses **two authenticated user types**:

### Company

- model: `companies.Company`
- this is the actual Django `AUTH_USER_MODEL`
- file: `companies/models.py`
- used for:
  - admin login
  - company dashboard
  - posting jobs
  - reviewing applicants
  - messaging seekers
  - scheduling interviews

### Seeker

- model: `seekers.Seeker`
- file: `seekers/models.py`
- custom auth-like model using its own backend
- used for:
  - seeker login
  - seeker dashboard
  - saving jobs
  - applying to jobs
  - messaging employers
  - receiving interview invites

### Backends

Configured in `config/settings.py`:

- `django.contrib.auth.backends.ModelBackend`
- `companies.backends.CompanyBackend`
- `seekers.backends.SeekerBackend`

Important:

- `AUTH_USER_MODEL = 'companies.Company'`
- seeker auth still works through its backend, but it is not the Django auth model

## 5. Current Core Data Model

### Jobs app

File: `jobs/models.py`

Models:

- `Category`
  - `name`
  - `slug`

- `TechStack`
  - `name`

- `Job`
  - `company`
  - `category`
  - `tech_stacks`
  - `title`
  - `description`
  - `requirements`
  - `experience_level`
  - `location`
  - `job_type`
  - `salary_range`
  - `apply_link`
  - `apply_email`
  - `plan`
  - `status`
  - `is_featured`
  - `views_count`
  - `date_posted`
  - `date_expires`

- `JobApplication`
  - `job`
  - `seeker`
  - `cover_note`
  - `status`
  - `date_applied`
  - unique constraint on `(job, seeker)`

- `ApplicationMessage`
  - linked to `JobApplication`
  - either `sender_company` or `sender_seeker`
  - `body`
  - `created_at`

- `ApplicationInterview`
  - linked to `JobApplication`
  - `scheduled_for`
  - `meeting_type`
  - `meeting_link`
  - `location`
  - `notes`
  - `status`
  - `created_at`

- `Notification`
  - either `recipient_company` or `recipient_seeker`
  - `title`
  - `body`
  - `link`
  - `is_read`
  - `created_at`

### Seeker model

File: `seekers/models.py`

Key fields:

- `email`
- `full_name`
- `phone`
- `location`
- `bio`
- `profile_photo` = `CloudinaryField`
- `experience_level`
- `availability`
- `github`
- `portfolio`
- `linkedin`
- `skills`
- `preferred_categories`
- `preferred_locations`
- `saved_jobs`
- `job_alerts_enabled`

Special:

- `groups` and `user_permissions` were overridden to avoid reverse accessor clashes with `Company`
- property `profile_photo_url` safely handles both Cloudinary values and legacy/local values

## 6. Major Functional Features Already Implemented

### Jobs and employer workflow

- companies can register/login/logout
- companies can post jobs
- first listing can be free
- jobs have plans (`free`, `basic`, `featured`)
- jobs require admin approval via status changes
- company dashboard shows:
  - total jobs
  - active jobs
  - pending jobs
  - total views
  - total applicants
- companies can review applicants per job
- companies can update application status
- companies can message applicants
- companies can schedule interviews
- companies receive notifications for:
  - new applications
  - candidate messages
  - interview responses

### Seeker workflow

- seekers can register/login/logout
- seekers can edit profile
- seeker profile photo uploads go to Cloudinary
- seekers can save jobs
- seekers can apply to jobs directly on the platform
- seekers can view application history
- seekers can participate in conversations
- seekers can accept/decline interview invites
- seekers receive notifications for:
  - application status updates
  - new employer messages
  - interview invites

### Notifications

- in-app notification center exists
- navbar shows unread badge
- notifications can be marked read one by one
- notifications can be marked read all at once

### Job alerts

- when job becomes active, job alerts can be sent to matching seekers
- emails are attempted on activation
- admin approval no longer crashes if email delivery is slow or unavailable

## 7. Important Fixes That Were Made

### Interpreter/editor issues

- VS Code/Pylance import problems were caused by wrong interpreter selection
- `.vscode/settings.json` was added to point to project venv

### Reverse accessor clash

- `Company` and `Seeker` both used permission-related fields
- `Seeker.groups` and `Seeker.user_permissions` were explicitly given unique related names

### Tech stack saving

- job form/save flow was fixed so:
  - `form.save_m2m()` is called
  - custom tech stacks are created/saved properly

### Company/seeker access separation

- seeker accounts were blocked from company-only actions
- company-only dashboard/posting/payment views now redirect seekers safely

### Contact form

- contact form was changed from fake success to actual email sending logic

### Render admin deployment error

- custom management command `createadmin` previously had no `Command` class
- fixed by implementing a proper Django management command

### Catalog seeding

- `seed_catalog` command added to create categories and tech stacks
- `build.sh` updated so Render deploy seeds catalog automatically

### Encoding cleanup

- many bad characters like `â€”`, `Ã©`, etc. were cleaned from models/templates/settings
- some old files may still contain minor text artifacts in places not yet fully normalized, but the major user-facing corruption was addressed

### Media/file handling

- media serving route was added for production fallback in `config/urls.py`
- seeker photos moved to Cloudinary because Render free tier storage is ephemeral

### Cloudinary integration

- `cloudinary` dependency added
- `Seeker.profile_photo` migrated to `CloudinaryField`
- explicit Cloudinary config added in settings
- profile edit flow changed to manual upload with `cloudinary.uploader.upload(...)`
- templates switched to safe `profile_photo_url`

### Job approval timeout fix

- approving a job in admin used to try synchronous SMTP sending and hit Render worker timeout
- `EMAIL_TIMEOUT` added
- admin activation now wraps alert sending in `try/except`

## 8. Current Routes / Workflow Surface

### Jobs URLs

File: `jobs/urls.py`

Key routes:

- `/jobs/`
- `/jobs/<pk>/`
- `/jobs/<pk>/apply/`
- `/jobs/<pk>/applicants/`
- `/applications/<pk>/status/`
- `/applications/<pk>/conversation/`
- `/applications/<pk>/schedule-interview/`
- `/interviews/<pk>/respond/`
- `/notifications/`
- `/notifications/<pk>/read/`
- `/notifications/read-all/`
- `/post-job/`

### Company URLs

File: `companies/urls.py`

Key routes:

- `/register/`
- `/login/`
- `/logout/`
- `/dashboard/`
- `/company/<pk>/`
- `/payment-info/`

### Seeker URLs

File: `seekers/urls.py`

Key routes:

- `/seeker/register/`
- `/seeker/login/`
- `/seeker/logout/`
- `/seeker/dashboard/`
- `/seeker/profile/`
- `/seeker/profile/edit/`
- `/seeker/applications/`
- `/seeker/saved-jobs/`
- `/seeker/save-job/<pk>/`
- `/seekers/`
- `/seekers/<pk>/`

## 9. UI/Design Work Completed

There has been a major UI pass to make the platform feel more professional and trustworthy.

### Public / shared surfaces

- `templates/pages/home.html`
  - redesigned into a premium employer-trust homepage
- `templates/navbar.html`
  - redesigned with stronger brand feel and better right-side account area
- `templates/footer.html`
  - redesigned with a more polished platform identity
- `templates/jobs/job_detail.html`
  - redesigned with better hierarchy, company trust cues, and action layout

### Employer-facing pages

- `templates/companies/dashboard.html`
  - redesigned into a recruiter-style workspace
- `templates/jobs/job_applicants.html`
  - redesigned into a candidate review board
- `templates/jobs/application_conversation.html`
  - redesigned into a cleaner hiring conversation/interview workspace

### Seeker-facing pages

- `templates/seekers/dashboard.html`
  - redesigned into a more polished candidate workspace
- `templates/seekers/my_applications.html`
  - redesigned application tracker
- `templates/jobs/notifications.html`
  - redesigned notifications center
- `templates/seekers/profile.html`
  - redesigned profile page
- `templates/seekers/edit_profile.html`
  - redesigned profile editor

### Auth / onboarding

- `templates/companies/login.html`
- `templates/companies/register.html`
- `templates/seekers/login.html`
- `templates/seekers/register.html`

All were redesigned into a more premium onboarding/auth style.

## 10. Admin / Management Commands

### Admin registrations

`jobs/admin.py` registers:

- `Category`
- `TechStack`
- `Job`
- `JobApplication`
- `ApplicationMessage`
- `ApplicationInterview`
- `Notification`

### Custom management commands

#### `createadmin`

Path:

- `companies/management/commands/createadmin.py`

Purpose:

- creates admin/superuser company account using env vars

Env vars used:

- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`
- `DJANGO_SUPERUSER_COMPANY_NAME`

#### `seed_catalog`

Path:

- `jobs/management/commands/seed_catalog.py`

Purpose:

- seeds default categories
- seeds default tech stacks
- idempotent

## 11. Deployment / Render Notes

### Important files

- `build.sh`
  - installs dependencies
  - collects static
  - migrates
  - seeds catalog
  - can run admin setup depending on setup

### Render environment variables to know

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `SITE_URL`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_TIMEOUT`
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`
- `DJANGO_SUPERUSER_COMPANY_NAME`
- `CLOUDINARY_URL`
- or alternatively:
  - `CLOUDINARY_CLOUD_NAME`
  - `CLOUDINARY_API_KEY`
  - `CLOUDINARY_API_SECRET`

### Important deployment realities

- seeker photos use Cloudinary because Render free tier local storage is ephemeral
- job approval no longer hard-fails on email timeout
- notifications are in-app, so even if email is imperfect, platform activity can still be tracked

## 12. Database Migration State

Known important `jobs` migrations:

- `0001_initial.py`
- `0002_techstack_job_experience_level_alter_job_location_and_more.py`
- `0003_alter_job_experience_level_alter_job_location.py`
- `0004_jobapplication.py`
- `0005_applicationmessage.py`
- `0006_applicationinterview.py`
- `0007_notification.py`

Known important `seekers` migration:

- `0003_alter_seeker_profile_photo_cloudinary.py`

## 13. Current Product Positioning

Recommended positioning:

- not just a job board
- a Cameroon tech hiring platform
- a place where employers can post, review, message, schedule, and manage early-stage hiring inside one workflow

### Strong current differentiators

- tech-focused rather than generic broad employment
- seeker/company dual ecosystem
- internal applications
- internal messaging
- interview scheduling
- notifications
- talent browsing

## 14. What Another AI Should Know Before Editing

- use the project venv:
  - `.\venv\Scripts\python.exe`
- this repo has both company and seeker auth flows; do not assume a single user model everywhere
- `Company` is `AUTH_USER_MODEL`
- `Seeker` is authenticated separately via backend
- do not break type separation between seeker-only and company-only views
- seeker profile photos are Cloudinary-backed
- notifications, applications, messaging, and interviews are all now linked through the `jobs` app
- many templates were recently redesigned inline with template-local CSS; large shared CSS refactors have not yet been done

## 15. Recommended Next Priorities

### Product / monetization

Best next product features:

1. employer shortlist + recruiter private notes
2. verified employer badges
3. featured jobs / paid visibility
4. recruiter subscription tiers
5. managed sourcing service

### Trust / public proof

Best public-site improvements:

1. testimonials
2. employer logos
3. “recently hired” / success stories
4. verified company visuals
5. recruiter analytics preview on landing pages

### Technical / future architecture

Best structural improvements:

1. move notification/email side effects into services/signals/tasks
2. background jobs for email and possibly alerts
3. normalize remaining encoding artifacts
4. unify more CSS into reusable shared system rather than per-template blocks
5. add automated tests for auth flow, applications, messaging, and interviews

## 16. Useful Commands

Run checks:

```powershell
.\venv\Scripts\python.exe manage.py check
```

Make migrations:

```powershell
.\venv\Scripts\python.exe manage.py makemigrations
```

Apply migrations:

```powershell
.\venv\Scripts\python.exe manage.py migrate
```

Run server:

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

Seed catalog locally:

```powershell
.\venv\Scripts\python.exe manage.py seed_catalog
```

Create admin locally:

```powershell
.\venv\Scripts\python.exe manage.py createadmin
```

## 17. Current High-Level State

The project is no longer just a simple Django job board.

It now has:

- a company hiring workspace
- a seeker career workspace
- direct applications
- application status tracking
- application conversations
- interview scheduling
- in-app notifications
- Cloudinary-backed seeker profile photos
- Render deployment support
- catalog seeding
- a significantly more professional UI across the main hiring flows

The most important unfinished work is now less about “core workflow exists” and more about:

- monetization
- trust proof
- premium recruiter features
- polishing remaining screens
- technical hardening

