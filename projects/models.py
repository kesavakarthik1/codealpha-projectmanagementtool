from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f'{self.user.username} – Profile'

    @property
    def display_name(self):
        full = self.user.get_full_name()
        return full if full else self.user.username

    def get_active_projects(self):
        """Projects this user owns or is a member of."""
        owned = self.user.owned_projects.all()
        member = self.user.member_projects.all()
        return (owned | member).distinct()


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class Project(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_ON_HOLD = 'on_hold'
    STATUS_COMPLETED = 'completed'
    STATUS_ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ON_HOLD, 'On Hold'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owned_projects'
    )
    members = models.ManyToManyField(
        User,
        through='ProjectMembership',
        related_name='member_projects',
        blank=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def is_member(self, user):
        """Return True if user is owner or a project member."""
        if self.owner == user:
            return True
        return self.memberships.filter(user=user).exists()

    def is_manager(self, user):
        """Return True if user is owner or has manager role."""
        if self.owner == user:
            return True
        return self.memberships.filter(user=user, role=ProjectMembership.ROLE_MANAGER).exists()

    def get_all_members(self):
        """Return all users (owner + members) as a queryset of User objects."""
        member_ids = list(self.memberships.values_list('user_id', flat=True))
        member_ids.append(self.owner_id)
        return User.objects.filter(id__in=member_ids).distinct()

    @property
    def task_count(self):
        return self.tasks.count()

    @property
    def completed_task_count(self):
        return self.tasks.filter(status=Task.STATUS_DONE).count()

    @property
    def member_count(self):
        # owner + members
        return self.memberships.count() + 1


# ---------------------------------------------------------------------------
# Project Membership
# ---------------------------------------------------------------------------

class ProjectMembership(models.Model):
    ROLE_MEMBER = 'member'
    ROLE_MANAGER = 'manager'

    ROLE_CHOICES = [
        (ROLE_MEMBER, 'Member'),
        (ROLE_MANAGER, 'Manager'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')
        ordering = ['joined_at']

    def __str__(self):
        return f'{self.user.username} – {self.project.name} ({self.role})'


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------

class Board(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='board')
    name = models.CharField(max_length=200, default='Main Board')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} – {self.project.name}'


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class Task(models.Model):
    STATUS_TODO = 'todo'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_REVIEW = 'review'
    STATUS_DONE = 'done'

    STATUS_CHOICES = [
        (STATUS_TODO, 'To Do'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_REVIEW, 'Review'),
        (STATUS_DONE, 'Done'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_URGENT, 'Urgent'),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    board = models.ForeignKey(
        Board, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def is_overdue(self):
        if self.due_date and self.status != self.STATUS_DONE:
            return self.due_date < timezone.now().date()
        return False

    def get_status_display_class(self):
        mapping = {
            self.STATUS_TODO: 'status-todo',
            self.STATUS_IN_PROGRESS: 'status-inprogress',
            self.STATUS_REVIEW: 'status-review',
            self.STATUS_DONE: 'status-done',
        }
        return mapping.get(self.status, '')

    def get_priority_display_class(self):
        mapping = {
            self.PRIORITY_LOW: 'priority-low',
            self.PRIORITY_MEDIUM: 'priority-medium',
            self.PRIORITY_HIGH: 'priority-high',
            self.PRIORITY_URGENT: 'priority-urgent',
        }
        return mapping.get(self.priority, '')


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author.username} on "{self.task.title}"'
