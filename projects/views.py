from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponseForbidden, Http404
from django.utils import timezone

from .models import Profile, Project, ProjectMembership, Board, Task, Comment
from .forms import (
    RegisterForm, LoginForm, ProfileForm,
    ProjectForm, AddMemberForm,
    TaskForm, TaskStatusForm,
    CommentForm, SearchForm,
)


# ===========================================================================
# Helpers
# ===========================================================================

def get_user_projects(user):
    """Return all projects where user is owner or member."""
    owned = Project.objects.filter(owner=user)
    member = Project.objects.filter(memberships__user=user)
    return (owned | member).distinct().order_by('-updated_at')


def require_project_access(request, project):
    """Raise 403 if request.user is not a member/owner of the project."""
    if not project.is_member(request.user):
        raise Http404("Project not found or access denied.")


def require_project_manager(request, project):
    """Raise 403 if request.user is not the owner/manager of the project."""
    if not project.is_manager(request.user):
        return HttpResponseForbidden("You don't have permission to manage this project.")
    return None


# ===========================================================================
# Home
# ===========================================================================

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'projects/home.html')


# ===========================================================================
# Authentication
# ===========================================================================

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to ProjectFlow, {user.username}! Your account has been created.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'projects/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'projects/login.html', {'form': form})


@login_required
def logout_view(request):
    if request.method == 'POST':
        username = request.user.username
        logout(request)
        messages.success(request, f'You have been logged out, {username}. See you soon!')
        return redirect('home')
    return redirect('dashboard')


# ===========================================================================
# Dashboard
# ===========================================================================

@login_required
def dashboard(request):
    user = request.user
    projects = get_user_projects(user)

    # Stats across all user projects
    project_ids = projects.values_list('id', flat=True)
    all_tasks = Task.objects.filter(project_id__in=project_ids)
    assigned_tasks = Task.objects.filter(assigned_to=user).select_related('project')

    stats = {
        'total_projects': projects.count(),
        'total_tasks': all_tasks.count(),
        'completed_tasks': all_tasks.filter(status=Task.STATUS_DONE).count(),
        'in_progress_tasks': all_tasks.filter(status=Task.STATUS_IN_PROGRESS).count(),
        'todo_tasks': all_tasks.filter(status=Task.STATUS_TODO).count(),
        'review_tasks': all_tasks.filter(status=Task.STATUS_REVIEW).count(),
        'high_urgent_tasks': all_tasks.filter(
            priority__in=[Task.PRIORITY_HIGH, Task.PRIORITY_URGENT]
        ).exclude(status=Task.STATUS_DONE).count(),
        'overdue_tasks': sum(1 for t in all_tasks if t.is_overdue),
    }

    recent_tasks = all_tasks.select_related('project', 'assigned_to').order_by('-updated_at')[:8]
    my_tasks = assigned_tasks.exclude(status=Task.STATUS_DONE).order_by('due_date')[:6]

    context = {
        'projects': projects[:6],
        'stats': stats,
        'recent_tasks': recent_tasks,
        'my_tasks': my_tasks,
    }
    return render(request, 'projects/dashboard.html', context)


# ===========================================================================
# Search
# ===========================================================================

@login_required
def search_view(request):
    form = SearchForm(request.GET)
    query = ''
    project_results = []
    task_results = []

    if form.is_valid():
        query = form.cleaned_data.get('q', '').strip()

    if query:
        user_projects = get_user_projects(request.user)
        project_ids = user_projects.values_list('id', flat=True)

        project_results = user_projects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

        task_results = Task.objects.filter(
            project_id__in=project_ids
        ).filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).select_related('project', 'assigned_to')

    total_results = 0
    if query:
        total_results = project_results.count() + task_results.count()

    context = {
        'form': form,
        'query': query,
        'project_results': project_results,
        'task_results': task_results,
        'total_results': total_results,
    }
    return render(request, 'projects/search.html', context)


# ===========================================================================
# Profile
# ===========================================================================

@login_required
def profile_view(request, username=None):
    if username:
        target_user = get_object_or_404(User, username=username)
    else:
        target_user = request.user

    profile, _ = Profile.objects.get_or_create(user=target_user)
    projects = get_user_projects(target_user)
    assigned_tasks_qs = Task.objects.filter(
        assigned_to=target_user
    ).select_related('project').order_by('-updated_at')
    assigned_tasks = assigned_tasks_qs[:10]   # sliced for display
    assigned_tasks_count = assigned_tasks_qs.count()

    context = {
        'profile_user': target_user,
        'profile': profile,
        'projects': projects,
        'assigned_tasks': assigned_tasks,
        'assigned_tasks_count': assigned_tasks_count,
        'is_own_profile': target_user == request.user,
    }
    return render(request, 'projects/profile.html', context)


@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'projects/profile_edit.html', {'form': form, 'profile': profile})


# ===========================================================================
# Projects – List / Create
# ===========================================================================

@login_required
def project_list(request):
    projects = get_user_projects(request.user).select_related('owner')
    context = {'projects': projects}
    return render(request, 'projects/project_list.html', context)


@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            # Signal creates the board automatically.
            messages.success(request, f'Project "{project.name}" has been created!')
            return redirect('project_detail', pk=project.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectForm()

    return render(request, 'projects/project_create.html', {'form': form})


# ===========================================================================
# Projects – Detail / Edit / Delete
# ===========================================================================

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    require_project_access(request, project)

    project_ids = [project.pk]
    tasks = Task.objects.filter(project=project).select_related('assigned_to', 'created_by')

    stats = {
        'total': tasks.count(),
        'todo': tasks.filter(status=Task.STATUS_TODO).count(),
        'in_progress': tasks.filter(status=Task.STATUS_IN_PROGRESS).count(),
        'review': tasks.filter(status=Task.STATUS_REVIEW).count(),
        'done': tasks.filter(status=Task.STATUS_DONE).count(),
        'high_urgent': tasks.filter(
            priority__in=[Task.PRIORITY_HIGH, Task.PRIORITY_URGENT]
        ).exclude(status=Task.STATUS_DONE).count(),
    }

    members = project.memberships.select_related('user', 'user__profile').all()
    recent_tasks = tasks.order_by('-updated_at')[:5]

    context = {
        'project': project,
        'stats': stats,
        'members': members,
        'recent_tasks': recent_tasks,
        'is_manager': project.is_manager(request.user),
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    response = require_project_manager(request, project)
    if response:
        return response

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project "{project.name}" has been updated.')
            return redirect('project_detail', pk=project.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectForm(instance=project)

    return render(request, 'projects/project_edit.html', {'form': form, 'project': project})


@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner != request.user:
        return HttpResponseForbidden("Only the project owner can delete this project.")

    if request.method == 'POST':
        name = project.name
        project.delete()
        messages.success(request, f'Project "{name}" has been deleted.')
        return redirect('project_list')

    return render(request, 'projects/project_confirm_delete.html', {'project': project})


# ===========================================================================
# Project Members
# ===========================================================================

@login_required
def project_members(request, pk):
    project = get_object_or_404(Project, pk=pk)
    require_project_access(request, project)

    memberships = project.memberships.select_related('user', 'user__profile').order_by('joined_at')
    add_form = AddMemberForm(project=project)
    is_manager = project.is_manager(request.user)

    context = {
        'project': project,
        'memberships': memberships,
        'add_form': add_form,
        'is_manager': is_manager,
    }
    return render(request, 'projects/project_members.html', context)


@login_required
def project_add_member(request, pk):
    project = get_object_or_404(Project, pk=pk)
    response = require_project_manager(request, project)
    if response:
        return response

    if request.method == 'POST':
        form = AddMemberForm(request.POST, project=project)
        if form.is_valid():
            username = form.cleaned_data['username']
            user = User.objects.get(username=username)
            ProjectMembership.objects.create(project=project, user=user)
            messages.success(request, f'"{username}" has been added to {project.name}.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    return redirect('project_members', pk=pk)


@login_required
def project_remove_member(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk)
    response = require_project_manager(request, project)
    if response:
        return response

    if request.method == 'POST':
        user_to_remove = get_object_or_404(User, pk=user_id)

        if user_to_remove == project.owner:
            messages.error(request, 'Cannot remove the project owner from the project.')
            return redirect('project_members', pk=pk)

        membership = ProjectMembership.objects.filter(project=project, user=user_to_remove).first()
        if membership:
            membership.delete()
            messages.success(request, f'"{user_to_remove.username}" has been removed from {project.name}.')
        else:
            messages.error(request, 'This user is not a member of the project.')

    return redirect('project_members', pk=pk)


@login_required
def project_change_member_role(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk)
    response = require_project_manager(request, project)
    if response:
        return response

    if request.method == 'POST':
        user_target = get_object_or_404(User, pk=user_id)
        new_role = request.POST.get('role')
        if new_role not in [ProjectMembership.ROLE_MEMBER, ProjectMembership.ROLE_MANAGER]:
            messages.error(request, 'Invalid role.')
            return redirect('project_members', pk=pk)

        membership = get_object_or_404(ProjectMembership, project=project, user=user_target)
        membership.role = new_role
        membership.save()
        messages.success(request, f'{user_target.username}\'s role updated to {membership.get_role_display()}.')

    return redirect('project_members', pk=pk)


# ===========================================================================
# Board
# ===========================================================================

@login_required
def board_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    require_project_access(request, project)

    board, _ = Board.objects.get_or_create(project=project, defaults={'name': 'Main Board'})

    tasks = Task.objects.filter(project=project).select_related('assigned_to', 'created_by')

    # Filter by assignee
    assignee_filter = request.GET.get('assignee', '')
    priority_filter = request.GET.get('priority', '')

    if assignee_filter:
        if assignee_filter == 'unassigned':
            tasks = tasks.filter(assigned_to__isnull=True)
        else:
            tasks = tasks.filter(assigned_to__username=assignee_filter)

    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    columns = {
        Task.STATUS_TODO: {
            'label': 'To Do',
            'key': Task.STATUS_TODO,
            'tasks': tasks.filter(status=Task.STATUS_TODO).order_by('-created_at'),
            'css_class': 'col-todo',
        },
        Task.STATUS_IN_PROGRESS: {
            'label': 'In Progress',
            'key': Task.STATUS_IN_PROGRESS,
            'tasks': tasks.filter(status=Task.STATUS_IN_PROGRESS).order_by('-created_at'),
            'css_class': 'col-inprogress',
        },
        Task.STATUS_REVIEW: {
            'label': 'Review',
            'key': Task.STATUS_REVIEW,
            'tasks': tasks.filter(status=Task.STATUS_REVIEW).order_by('-created_at'),
            'css_class': 'col-review',
        },
        Task.STATUS_DONE: {
            'label': 'Done',
            'key': Task.STATUS_DONE,
            'tasks': tasks.filter(status=Task.STATUS_DONE).order_by('-created_at'),
            'css_class': 'col-done',
        },
    }

    members = project.get_all_members().order_by('username')

    context = {
        'project': project,
        'board': board,
        'columns': columns,
        'members': members,
        'assignee_filter': assignee_filter,
        'priority_filter': priority_filter,
        'priority_choices': Task.PRIORITY_CHOICES,
        'is_manager': project.is_manager(request.user),
        'status_choices': Task.STATUS_CHOICES,
    }
    return render(request, 'projects/board.html', context)


# ===========================================================================
# Tasks – Create
# ===========================================================================

@login_required
def task_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    require_project_access(request, project)

    board, _ = Board.objects.get_or_create(project=project, defaults={'name': 'Main Board'})

    initial = {}
    status_param = request.GET.get('status', '')
    if status_param in dict(Task.STATUS_CHOICES):
        initial['status'] = status_param

    if request.method == 'POST':
        form = TaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.board = board
            task.created_by = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" has been created.')
            next_url = request.POST.get('next', '')
            if next_url == 'board':
                return redirect('board', pk=project.pk)
            return redirect('task_detail', pk=task.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskForm(project=project, initial=initial)

    return render(request, 'projects/task_create.html', {
        'form': form,
        'project': project,
    })


# ===========================================================================
# Tasks – Detail
# ===========================================================================

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task.objects.select_related(
        'project', 'assigned_to', 'created_by', 'board'
    ), pk=pk)
    require_project_access(request, task.project)

    comments = task.comments.select_related('author', 'author__profile').order_by('created_at')
    comment_form = CommentForm()
    status_form = TaskStatusForm(instance=task)

    context = {
        'task': task,
        'comments': comments,
        'comment_form': comment_form,
        'status_form': status_form,
        'is_manager': task.project.is_manager(request.user),
        'can_edit': (
            task.project.is_manager(request.user)
            or task.created_by == request.user
            or task.assigned_to == request.user
        ),
    }
    return render(request, 'projects/task_detail.html', context)


# ===========================================================================
# Tasks – Edit
# ===========================================================================

@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    require_project_access(request, task.project)

    can_edit = (
        task.project.is_manager(request.user)
        or task.created_by == request.user
        or task.assigned_to == request.user
    )
    if not can_edit:
        return HttpResponseForbidden("You don't have permission to edit this task.")

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, project=task.project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" has been updated.')
            return redirect('task_detail', pk=task.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskForm(instance=task, project=task.project)

    return render(request, 'projects/task_edit.html', {
        'form': form,
        'task': task,
        'project': task.project,
    })


# ===========================================================================
# Tasks – Delete
# ===========================================================================

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    require_project_access(request, task.project)

    can_delete = (
        task.project.is_manager(request.user)
        or task.created_by == request.user
    )
    if not can_delete:
        return HttpResponseForbidden("You don't have permission to delete this task.")

    project = task.project
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" has been deleted.')
        return redirect('board', pk=project.pk)

    return render(request, 'projects/task_confirm_delete.html', {
        'task': task,
        'project': project,
    })


# ===========================================================================
# Tasks – Change Status (AJAX-friendly POST)
# ===========================================================================

@login_required
def task_change_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    require_project_access(request, task.project)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = dict(Task.STATUS_CHOICES).keys()
        if new_status in valid_statuses:
            task.status = new_status
            task.save(update_fields=['status', 'updated_at'])
            messages.success(
                request,
                f'Task "{task.title}" moved to {task.get_status_display()}.'
            )
        else:
            messages.error(request, 'Invalid status value.')

    next_url = request.POST.get('next', '')
    if next_url == 'board':
        return redirect('board', pk=task.project.pk)
    return redirect('task_detail', pk=task.pk)


# ===========================================================================
# Comments – Create / Delete
# ===========================================================================

@login_required
def comment_create(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    require_project_access(request, task.project)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    return redirect('task_detail', pk=task.pk)


@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    task = comment.task
    require_project_access(request, task.project)

    can_delete = (
        comment.author == request.user
        or task.project.is_manager(request.user)
    )
    if not can_delete:
        return HttpResponseForbidden("You can't delete this comment.")

    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted.')

    return redirect('task_detail', pk=task.pk)
