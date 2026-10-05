# ProjectFlow – Project Management Tool

**CodeAlpha Full Stack Development Internship — Task 3: Project Management Tool**

---

## Project Overview

ProjectFlow is a full-stack collaborative project management web application built with Python and Django. It enables teams to create projects, manage members, organise work on Kanban-style boards, assign and track tasks, and communicate through task comments — all in a secure, authenticated environment.

The application is conceptually similar to a simplified Trello or Asana, built entirely from scratch using only the technologies specified for the CodeAlpha Task 3 assignment.

---

## Features

### Authentication & Users
- User registration with username, email, password, and optional full name
- Secure login / logout using Django's built-in session authentication
- Password hashing via Django's default PBKDF2 algorithm (no plaintext passwords)
- User profiles with bio, display name, and activity overview
- Profile editing (own profile only)

### Projects
- Create, view, edit, and delete projects
- Project status tracking: Active, On Hold, Completed, Archived
- Project overview dashboard with task statistics and progress bar
- Project list showing all accessible projects

### Project Members
- Add registered users to a project by username
- Remove members (owner protected from removal)
- Assign member roles: Member or Manager
- Duplicate membership prevention
- Access control: only members can see project data

### Project Boards
- Kanban-style board with four columns: **To Do**, **In Progress**, **Review**, **Done**
- Filter board by assignee and priority
- Client-side title search filter (vanilla JS)
- One board automatically created per project

### Task Cards
- Create, view, edit, and delete tasks
- Task card displays: title, short description, assignee avatar, priority badge, due date, comment count
- Priority colour-coded left border on cards
- Quick status change via inline select on each card
- Full task detail page

### Task Management
- Task fields: title, description, status, priority, assignee, due date
- Assignee restricted to project members only
- Priority levels: Low, Medium, High, Urgent
- Overdue detection (past due date + not done)
- Status radio buttons on task detail for quick changes

### Task Comments
- Threaded comments on every task
- Comment author, timestamp, and content displayed
- Delete own comment; project managers can moderate all comments
- Empty / whitespace-only comment rejection
- Character counter on comment textarea

### Dashboard
- Personal dashboard showing stats across all accessible projects
- Statistics: total projects, total tasks, in progress, in review, completed, high/urgent
- "My Open Tasks" widget
- Recent task activity feed
- Quick-access project cards

### Search
- Search projects and tasks by keyword
- Results scoped to projects the user can access
- Instant results page with separate project and task sections

### Admin
- Full Django admin interface for all models
- List displays, filters, and search configured for every model
- ProfileInline within User admin

---

## Technology Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3.10+ · Django 5.1+          |
| Database   | SQLite (Django ORM)                 |
| Frontend   | HTML5 · CSS3 · Vanilla JavaScript   |
| Templates  | Django Template Language (DTL)      |
| Auth       | Django built-in authentication      |
| Admin      | Django Admin                        |

**No Bootstrap, Tailwind, React, Vue, Angular, Node.js, or any frontend/backend framework beyond Django.**

---

## Architecture

```
Browser  ──►  Django URL Router  ──►  View (views.py)
                                         │
                                   Django ORM
                                         │
                                    SQLite DB
                                         │
                              Django Template Engine
                                         │
                               HTML + CSS + JS
                                    ◄──
```

The application follows a classic server-rendered MVC pattern:

- **Models** (`models.py`) define the data structure and business logic
- **Views** (`views.py`) handle HTTP requests, query the database, and return rendered responses
- **Templates** (`templates/projects/`) render HTML using context from views
- **Static files** (`static/projects/`) hold CSS and JavaScript served alongside HTML
- **Signals** (`signals.py`) auto-create Profiles and Boards when Users/Projects are saved

---

## Project Structure

```
CodeAlpha_ProjectManagementTool/
│
├── manage.py
│
├── projectmanager/               # Django project package
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── projects/                     # Main Django app
│   ├── migrations/
│   ├── templates/
│   │   └── projects/
│   │       ├── base.html
│   │       ├── home.html
│   │       ├── dashboard.html
│   │       ├── login.html
│   │       ├── register.html
│   │       ├── profile.html
│   │       ├── profile_edit.html
│   │       ├── project_list.html
│   │       ├── project_detail.html
│   │       ├── project_create.html
│   │       ├── project_edit.html
│   │       ├── project_confirm_delete.html
│   │       ├── project_members.html
│   │       ├── board.html
│   │       ├── task_detail.html
│   │       ├── task_create.html
│   │       ├── task_edit.html
│   │       ├── task_confirm_delete.html
│   │       └── search.html
│   │
│   ├── static/
│   │   └── projects/
│   │       ├── css/style.css
│   │       └── js/main.js
│   │
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py
│   │
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── signals.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
│
├── static/                       # Project-level static files
├── db.sqlite3                    # SQLite database (auto-created)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Database Models

### Profile
| Field       | Type              | Description                    |
|-------------|-------------------|--------------------------------|
| user        | OneToOneField     | Links to Django User           |
| bio         | TextField         | Optional biography             |
| created_at  | DateTimeField     | Auto set on creation           |
| updated_at  | DateTimeField     | Auto set on update             |

### Project
| Field       | Type              | Description                    |
|-------------|-------------------|--------------------------------|
| name        | CharField         | Project name                   |
| description | TextField         | Project description            |
| owner       | ForeignKey(User)  | Project creator/owner          |
| members     | ManyToManyField   | Via ProjectMembership          |
| status      | CharField         | active/on_hold/completed/archived |
| created_at  | DateTimeField     |                                |
| updated_at  | DateTimeField     |                                |

### ProjectMembership
| Field      | Type             | Description                     |
|------------|------------------|---------------------------------|
| project    | ForeignKey       |                                 |
| user       | ForeignKey       |                                 |
| role       | CharField        | member / manager                |
| joined_at  | DateTimeField    | Auto set                        |

### Board
| Field      | Type             | Description                     |
|------------|------------------|---------------------------------|
| project    | OneToOneField    | One board per project           |
| name       | CharField        | Board name                      |
| created_at | DateTimeField    |                                 |
| updated_at | DateTimeField    |                                 |

### Task
| Field       | Type              | Description                    |
|-------------|-------------------|--------------------------------|
| title       | CharField         |                                |
| description | TextField         |                                |
| project     | ForeignKey        |                                |
| board       | ForeignKey        |                                |
| status      | CharField         | todo/in_progress/review/done   |
| priority    | CharField         | low/medium/high/urgent         |
| assigned_to | ForeignKey(User)  | Nullable                       |
| created_by  | ForeignKey(User)  |                                |
| due_date    | DateField         | Nullable                       |
| created_at  | DateTimeField     |                                |
| updated_at  | DateTimeField     |                                |

### Comment
| Field      | Type             | Description                     |
|------------|------------------|---------------------------------|
| task       | ForeignKey       |                                 |
| author     | ForeignKey(User) |                                 |
| content    | TextField        |                                 |
| created_at | DateTimeField    |                                 |
| updated_at | DateTimeField    |                                 |

---

## Prerequisites

- Python 3.10 or higher (developed on Python 3.14)
- pip

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/CodeAlpha_ProjectManagementTool.git
cd CodeAlpha_ProjectManagementTool
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Load sample data (recommended)

```bash
python manage.py seed_data
```

This creates:
- **6 demo users** (password for all: `Demo1234!`)
  - `alice_dev` — Project owner (E-Commerce)
  - `carol_pm` — Project owner (Mobile App, HR Portal)
  - `frank_devops` — Project owner (Infrastructure)
  - `bob_design`, `dave_backend`, `eva_qa` — Team members
- **4 projects** with memberships and roles
- **19 tasks** across all statuses and priorities
- **20+ comments** demonstrating team communication

To reset and reseed:
```bash
python manage.py seed_data --flush
```

### 6. Create a Django superuser (for admin panel)

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

The application will be available at: **http://127.0.0.1:8000/**

---

## Django Admin

Access the admin panel at: **http://127.0.0.1:8000/admin/**

Log in with your superuser credentials to manage:
- Users and Profiles
- Projects and Project Memberships
- Boards
- Tasks
- Comments

---

## Running Tests

```bash
# Run all tests
python manage.py test projects

# Run with verbose output
python manage.py test projects --verbosity=2
```

The test suite covers:
- Registration and login/logout
- Profile creation and editing
- Project creation and access control
- Project member management
- Board access
- Task CRUD operations with permission checks
- Comment creation and deletion
- URL manipulation / permission bypass prevention
- Dashboard statistics
- Model methods
- Search functionality

---

## Main URLs

| URL                                    | View                  | Description               |
|----------------------------------------|-----------------------|---------------------------|
| `/`                                    | home                  | Landing page              |
| `/register/`                           | register_view         | User registration         |
| `/login/`                              | login_view            | Login                     |
| `/logout/`                             | logout_view           | Logout                    |
| `/dashboard/`                          | dashboard             | User dashboard            |
| `/search/`                             | search_view           | Search                    |
| `/profile/`                            | profile_view          | Own profile               |
| `/profile/edit/`                       | profile_edit          | Edit own profile          |
| `/profile/<username>/`                 | user_profile          | View another user         |
| `/projects/`                           | project_list          | All accessible projects   |
| `/projects/create/`                    | project_create        | Create project            |
| `/projects/<pk>/`                      | project_detail        | Project overview          |
| `/projects/<pk>/edit/`                 | project_edit          | Edit project              |
| `/projects/<pk>/delete/`               | project_delete        | Delete project            |
| `/projects/<pk>/members/`              | project_members       | Manage members            |
| `/projects/<pk>/board/`                | board_view            | Kanban board              |
| `/projects/<pk>/tasks/create/`         | task_create           | Create task               |
| `/tasks/<pk>/`                         | task_detail           | Task detail               |
| `/tasks/<pk>/edit/`                    | task_edit             | Edit task                 |
| `/tasks/<pk>/delete/`                  | task_delete           | Delete task               |
| `/tasks/<pk>/status/`                  | task_change_status    | Change task status        |
| `/tasks/<pk>/comments/add/`            | comment_create        | Add comment               |
| `/comments/<pk>/delete/`               | comment_delete        | Delete comment            |
| `/admin/`                              | Django admin          | Admin panel               |

---

## Application Usage

### Getting Started
1. Navigate to `http://127.0.0.1:8000/`
2. Click **Get Started Free** to register, or use a demo account
3. After login you'll land on your **Dashboard**

### Creating a Project
1. Click **+ New Project** in the navigation or dashboard
2. Enter a name, description, and status
3. A board is automatically created
4. You are automatically set as the project owner

### Managing Team Members
1. Open a project → click **Members** in the project subnav
2. Enter a registered user's username in the **Add Member** sidebar
3. Change member roles (Member / Manager) using the role select
4. Remove members with the **Remove** button

### Using the Board
1. Open a project → click **Board**
2. Tasks are grouped in four columns by status
3. Use the **status dropdown** on each card to move tasks between columns
4. Filter by assignee or priority using the filter bar
5. Click a task title to open the full detail view
6. Click **+** on a column header to create a task pre-set to that status

### Creating and Assigning Tasks
1. Click **+ New Task** from the board or project overview
2. Fill in title, description, status, priority, assignee, and optional due date
3. The assignee dropdown only shows project members

### Commenting on Tasks
1. Open a task detail page
2. Scroll to the **Comments** section
3. Type your comment and click **Post Comment**
4. Delete your own comments; project managers can delete any comment

---

## Screenshots

> _Screenshots to be added after running the application._

| Page                | Description                              |
|---------------------|------------------------------------------|
| Home page           | Landing page with feature highlights     |
| Dashboard           | Stats, my tasks, recent activity         |
| Project list        | Table of all accessible projects         |
| Project detail      | Overview with stats and member sidebar   |
| Board view          | Kanban columns with task cards           |
| Task detail         | Full task info with comments             |
| Project members     | Member list with role management         |
| Profile             | User profile with projects and tasks     |

---

## Security

- All views protected by `@login_required` or equivalent checks
- Project/task access verified against membership on every request
- CSRF protection on all POST forms
- All form data validated server-side
- Django's secure password hashing (PBKDF2-SHA256)
- Non-members receive HTTP 404 (not 403) to avoid information leakage

---

## CodeAlpha Task 3 Compliance

| Requirement                                      | Status      |
|--------------------------------------------------|-------------|
| Create group projects                            | ✅ Implemented |
| Assign tasks to project members                  | ✅ Implemented |
| Comment and communicate within tasks             | ✅ Implemented |
| Authentication system (register/login/logout)    | ✅ Implemented |
| Project boards (Kanban)                          | ✅ Implemented |
| Task cards                                       | ✅ Implemented |
| Backend management (admin + full CRUD)           | ✅ Implemented |
| Notifications / real-time updates (WebSockets)   | 🔲 Bonus – not implemented |

---

## Future Improvements

- **Real-time updates** using Django Channels and WebSockets (bonus feature)
- **Notifications** when tasks are assigned or commented on
- **File attachments** on tasks
- **Task sub-tasks / checklists**
- **Activity log / audit trail** per project
- **Drag-and-drop** board reordering (saving via AJAX to Django)
- **Email notifications** on key events
- **Project templates**
- **Time tracking** on tasks
- **Gantt chart** view

---

## License

This project was created for the **CodeAlpha Full Stack Development Internship – Task 3**.  
For educational and demonstration purposes.
