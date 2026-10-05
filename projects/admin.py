from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile, Project, ProjectMembership, Board, Task, Comment


# ---------------------------------------------------------------------------
# Inline: Profile inside User admin
# ---------------------------------------------------------------------------

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('bio',)


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'bio')
    ordering = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')

    def display_name(self, obj):
        return obj.display_name
    display_name.short_description = 'Display Name'


# ---------------------------------------------------------------------------
# Project Membership Inline
# ---------------------------------------------------------------------------

class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1
    autocomplete_fields = ['user']


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'member_count', 'task_count', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'description', 'owner__username')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProjectMembershipInline]

    def member_count(self, obj):
        return obj.member_count
    member_count.short_description = 'Members'

    def task_count(self, obj):
        return obj.task_count
    task_count.short_description = 'Tasks'


# ---------------------------------------------------------------------------
# Project Membership
# ---------------------------------------------------------------------------

@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__username', 'project__name')
    ordering = ('-joined_at',)
    readonly_fields = ('joined_at',)


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'created_at')
    search_fields = ('name', 'project__name')
    ordering = ('project__name',)
    readonly_fields = ('created_at', 'updated_at')


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'project', 'status', 'priority',
        'assigned_to', 'created_by', 'due_date', 'created_at'
    )
    list_filter = ('status', 'priority', 'project', 'due_date')
    search_fields = ('title', 'description', 'project__name', 'assigned_to__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('assigned_to', 'created_by')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Task Info', {
            'fields': ('title', 'description', 'project', 'board')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'due_date')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'task', 'short_content', 'created_at', 'updated_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username', 'task__title')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def short_content(self, obj):
        return obj.content[:80] + '…' if len(obj.content) > 80 else obj.content
    short_content.short_description = 'Content'
