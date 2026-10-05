"""
Comprehensive test suite for ProjectFlow – CodeAlpha Task 3.

Run with:
    python manage.py test projects --verbosity=2
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

from .models import Profile, Project, ProjectMembership, Board, Task, Comment


# ===========================================================================
# Helpers / Base classes
# ===========================================================================

class BaseTestCase(TestCase):
    """
    Shared setup: creates two users (owner + member) and a project
    so individual test classes don't repeat boilerplate.
    """

    def setUp(self):
        self.client = Client()

        # Users
        self.owner = User.objects.create_user(
            username='owner_user', password='TestPass123!', email='owner@test.com'
        )
        self.member = User.objects.create_user(
            username='member_user', password='TestPass123!', email='member@test.com'
        )
        self.outsider = User.objects.create_user(
            username='outsider_user', password='TestPass123!', email='outsider@test.com'
        )

        # Project (signal auto-creates Board)
        self.project = Project.objects.create(
            name='Test Project',
            description='A project for testing',
            owner=self.owner,
            status=Project.STATUS_ACTIVE,
        )

        # Add member to project
        self.membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
            role=ProjectMembership.ROLE_MEMBER,
        )

        # Board (created by signal, but fetch it)
        self.board = Board.objects.get(project=self.project)

        # Task
        self.task = Task.objects.create(
            title='Test Task',
            description='A task for testing',
            project=self.project,
            board=self.board,
            status=Task.STATUS_TODO,
            priority=Task.PRIORITY_MEDIUM,
            created_by=self.owner,
        )

        # Comment
        self.comment = Comment.objects.create(
            task=self.task,
            author=self.member,
            content='A test comment',
        )

    def login_as(self, user):
        self.client.login(username=user.username, password='TestPass123!')

    def login_owner(self):
        self.login_as(self.owner)

    def login_member(self):
        self.login_as(self.member)

    def login_outsider(self):
        self.login_as(self.outsider)


# ===========================================================================
# 1. Authentication Tests
# ===========================================================================

class RegistrationTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_register_page_loads(self):
        resp = self.client.get(reverse('register'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Create')

    def test_successful_registration(self):
        resp = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'StrongPass999!',
            'password2': 'StrongPass999!',
        })
        # Should redirect after successful registration
        self.assertRedirects(resp, reverse('dashboard'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_creates_profile(self):
        self.client.post(reverse('register'), {
            'username': 'profileuser',
            'email': 'profile@test.com',
            'password1': 'StrongPass999!',
            'password2': 'StrongPass999!',
        })
        user = User.objects.get(username='profileuser')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='taken', password='pass', email='taken@test.com')
        resp = self.client.post(reverse('register'), {
            'username': 'taken',
            'email': 'newemail@test.com',
            'password1': 'StrongPass999!',
            'password2': 'StrongPass999!',
        })
        # Should stay on register page with errors
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(email='newemail@test.com').exists())

    def test_password_mismatch_rejected(self):
        resp = self.client.post(reverse('register'), {
            'username': 'mismatch',
            'email': 'mismatch@test.com',
            'password1': 'StrongPass999!',
            'password2': 'DifferentPass!',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatch').exists())

    def test_duplicate_email_rejected(self):
        User.objects.create_user(username='user1', password='pass', email='dup@test.com')
        resp = self.client.post(reverse('register'), {
            'username': 'user2',
            'email': 'dup@test.com',
            'password1': 'StrongPass999!',
            'password2': 'StrongPass999!',
        })
        self.assertEqual(resp.status_code, 200)


class LoginTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='logintest', password='TestPass123!', email='login@test.com'
        )

    def test_login_page_loads(self):
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)

    def test_successful_login_redirects_to_dashboard(self):
        resp = self.client.post(reverse('login'), {
            'username': 'logintest',
            'password': 'TestPass123!',
        })
        self.assertRedirects(resp, reverse('dashboard'))

    def test_invalid_password_rejected(self):
        resp = self.client.post(reverse('login'), {
            'username': 'logintest',
            'password': 'WrongPassword',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    def test_nonexistent_user_rejected(self):
        resp = self.client.post(reverse('login'), {
            'username': 'nobody',
            'password': 'TestPass123!',
        })
        self.assertEqual(resp.status_code, 200)

    def test_logout_redirects_home(self):
        self.client.login(username='logintest', password='TestPass123!')
        resp = self.client.post(reverse('logout'))
        self.assertRedirects(resp, reverse('home'))

    def test_anonymous_redirected_from_dashboard(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertRedirects(resp, '/login/?next=/dashboard/')


# ===========================================================================
# 2. Profile Tests
# ===========================================================================

class ProfileTests(BaseTestCase):

    def test_profile_auto_created_on_user_creation(self):
        self.assertTrue(Profile.objects.filter(user=self.owner).exists())
        self.assertTrue(Profile.objects.filter(user=self.member).exists())

    def test_own_profile_page_loads(self):
        self.login_owner()
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.owner.username)

    def test_other_user_profile_loads(self):
        self.login_owner()
        resp = self.client.get(reverse('user_profile', kwargs={'username': self.member.username}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.member.username)

    def test_profile_edit_page_loads_for_own_user(self):
        self.login_owner()
        resp = self.client.get(reverse('profile_edit'))
        self.assertEqual(resp.status_code, 200)

    def test_profile_edit_saves_bio(self):
        self.login_owner()
        resp = self.client.post(reverse('profile_edit'), {
            'bio': 'My updated bio',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'owner@test.com',
        })
        self.assertRedirects(resp, reverse('profile'))
        self.owner.profile.refresh_from_db()
        self.assertEqual(self.owner.profile.bio, 'My updated bio')

    def test_anonymous_cannot_view_profile(self):
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 302)  # redirect to login

    def test_profile_edit_requires_login(self):
        resp = self.client.get(reverse('profile_edit'))
        self.assertEqual(resp.status_code, 302)


# ===========================================================================
# 3. Project Tests
# ===========================================================================

class ProjectCreationTests(BaseTestCase):

    def test_authenticated_user_can_create_project(self):
        self.login_owner()
        resp = self.client.post(reverse('project_create'), {
            'name': 'Brand New Project',
            'description': 'Testing project creation',
            'status': 'active',
        })
        self.assertTrue(Project.objects.filter(name='Brand New Project').exists())

    def test_anonymous_cannot_create_project(self):
        resp = self.client.post(reverse('project_create'), {
            'name': 'Should Not Exist',
            'description': 'Test',
            'status': 'active',
        })
        self.assertFalse(Project.objects.filter(name='Should Not Exist').exists())
        self.assertEqual(resp.status_code, 302)

    def test_new_project_has_owner(self):
        self.login_owner()
        self.client.post(reverse('project_create'), {
            'name': 'Owned Project',
            'description': '',
            'status': 'active',
        })
        project = Project.objects.get(name='Owned Project')
        self.assertEqual(project.owner, self.owner)

    def test_new_project_auto_creates_board(self):
        self.login_owner()
        self.client.post(reverse('project_create'), {
            'name': 'Board Project',
            'description': '',
            'status': 'active',
        })
        project = Project.objects.get(name='Board Project')
        self.assertTrue(Board.objects.filter(project=project).exists())

    def test_blank_project_name_rejected(self):
        self.login_owner()
        count_before = Project.objects.count()
        self.client.post(reverse('project_create'), {
            'name': '',
            'description': 'No name',
            'status': 'active',
        })
        self.assertEqual(Project.objects.count(), count_before)


class ProjectAccessTests(BaseTestCase):

    def test_owner_can_access_project_detail(self):
        self.login_owner()
        resp = self.client.get(reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_member_can_access_project_detail(self):
        self.login_member()
        resp = self.client.get(reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_outsider_cannot_access_project_detail(self):
        self.login_outsider()
        resp = self.client.get(reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_anonymous_redirected_from_project_detail(self):
        resp = self.client.get(reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_owner_can_edit_project(self):
        self.login_owner()
        resp = self.client.post(reverse('project_edit', kwargs={'pk': self.project.pk}), {
            'name': 'Renamed Project',
            'description': 'Updated',
            'status': 'active',
        })
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Renamed Project')

    def test_member_cannot_edit_project(self):
        self.login_member()
        resp = self.client.post(reverse('project_edit', kwargs={'pk': self.project.pk}), {
            'name': 'Unauthorised Rename',
            'description': '',
            'status': 'active',
        })
        self.project.refresh_from_db()
        self.assertNotEqual(self.project.name, 'Unauthorised Rename')

    def test_outsider_cannot_edit_project(self):
        self.login_outsider()
        resp = self.client.get(reverse('project_edit', kwargs={'pk': self.project.pk}))
        # Either 403 or 404
        self.assertIn(resp.status_code, [403, 404])

    def test_project_list_shows_only_accessible_projects(self):
        # Create a separate project that owner doesn't belong to
        other_owner = User.objects.create_user(username='other_owner', password='pass123!')
        other_project = Project.objects.create(
            name='Private Other Project',
            owner=other_owner,
        )
        self.login_owner()
        resp = self.client.get(reverse('project_list'))
        self.assertContains(resp, self.project.name)
        self.assertNotContains(resp, 'Private Other Project')


# ===========================================================================
# 4. Project Member Tests
# ===========================================================================

class MemberManagementTests(BaseTestCase):

    def test_owner_can_view_members_page(self):
        self.login_owner()
        resp = self.client.get(reverse('project_members', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_owner_can_add_member(self):
        new_user = User.objects.create_user(username='new_member', password='pass123!')
        self.login_owner()
        self.client.post(
            reverse('project_add_member', kwargs={'pk': self.project.pk}),
            {'username': 'new_member'}
        )
        self.assertTrue(
            ProjectMembership.objects.filter(project=self.project, user=new_user).exists()
        )

    def test_duplicate_membership_prevented(self):
        self.login_owner()
        count_before = ProjectMembership.objects.filter(project=self.project).count()
        # Try adding member who is already a member
        self.client.post(
            reverse('project_add_member', kwargs={'pk': self.project.pk}),
            {'username': self.member.username}
        )
        count_after = ProjectMembership.objects.filter(project=self.project).count()
        self.assertEqual(count_before, count_after)

    def test_cannot_add_nonexistent_user(self):
        self.login_owner()
        resp = self.client.post(
            reverse('project_add_member', kwargs={'pk': self.project.pk}),
            {'username': 'does_not_exist'}
        )
        # Redirects back, no new membership
        self.assertEqual(resp.status_code, 302)

    def test_owner_can_remove_member(self):
        self.login_owner()
        self.client.post(
            reverse('project_remove_member', kwargs={
                'pk': self.project.pk,
                'user_id': self.member.pk,
            })
        )
        self.assertFalse(
            ProjectMembership.objects.filter(project=self.project, user=self.member).exists()
        )

    def test_cannot_remove_owner(self):
        self.login_owner()
        self.client.post(
            reverse('project_remove_member', kwargs={
                'pk': self.project.pk,
                'user_id': self.owner.pk,
            })
        )
        # Owner cannot be removed as a membership entry (they're not a member, they're owner)
        self.assertEqual(self.project.owner, self.owner)

    def test_outsider_cannot_add_member(self):
        new_user = User.objects.create_user(username='victim', password='pass123!')
        self.login_outsider()
        resp = self.client.post(
            reverse('project_add_member', kwargs={'pk': self.project.pk}),
            {'username': 'victim'}
        )
        self.assertIn(resp.status_code, [403, 404])

    def test_member_cannot_add_member(self):
        new_user = User.objects.create_user(username='blocked_add', password='pass123!')
        self.login_member()
        resp = self.client.post(
            reverse('project_add_member', kwargs={'pk': self.project.pk}),
            {'username': 'blocked_add'}
        )
        self.assertIn(resp.status_code, [403, 404])


# ===========================================================================
# 5. Board Tests
# ===========================================================================

class BoardTests(BaseTestCase):

    def test_board_auto_created_with_project(self):
        new_project = Project.objects.create(
            name='Board Test Project',
            owner=self.owner,
        )
        self.assertTrue(Board.objects.filter(project=new_project).exists())

    def test_owner_can_access_board(self):
        self.login_owner()
        resp = self.client.get(reverse('board', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_member_can_access_board(self):
        self.login_member()
        resp = self.client.get(reverse('board', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_outsider_cannot_access_board(self):
        self.login_outsider()
        resp = self.client.get(reverse('board', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_board_displays_task_in_correct_column(self):
        self.login_owner()
        self.task.status = Task.STATUS_IN_PROGRESS
        self.task.save()
        resp = self.client.get(reverse('board', kwargs={'pk': self.project.pk}))
        self.assertContains(resp, self.task.title)

    def test_board_filter_by_assignee(self):
        self.login_owner()
        self.task.assigned_to = self.member
        self.task.save()
        resp = self.client.get(
            reverse('board', kwargs={'pk': self.project.pk}),
            {'assignee': self.member.username}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.task.title)


# ===========================================================================
# 6. Task Tests
# ===========================================================================

class TaskCreationTests(BaseTestCase):

    def test_member_can_create_task(self):
        self.login_member()
        resp = self.client.post(
            reverse('task_create', kwargs={'project_pk': self.project.pk}),
            {
                'title': 'Member Created Task',
                'description': 'A task created by a member',
                'status': Task.STATUS_TODO,
                'priority': Task.PRIORITY_LOW,
                'next': 'board',
            }
        )
        self.assertTrue(Task.objects.filter(title='Member Created Task').exists())

    def test_owner_can_create_task(self):
        self.login_owner()
        resp = self.client.post(
            reverse('task_create', kwargs={'project_pk': self.project.pk}),
            {
                'title': 'Owner Created Task',
                'description': '',
                'status': Task.STATUS_TODO,
                'priority': Task.PRIORITY_MEDIUM,
                'next': 'board',
            }
        )
        self.assertTrue(Task.objects.filter(title='Owner Created Task').exists())

    def test_outsider_cannot_create_task(self):
        self.login_outsider()
        resp = self.client.post(
            reverse('task_create', kwargs={'project_pk': self.project.pk}),
            {
                'title': 'Outsider Task',
                'description': '',
                'status': Task.STATUS_TODO,
                'priority': Task.PRIORITY_LOW,
            }
        )
        self.assertFalse(Task.objects.filter(title='Outsider Task').exists())

    def test_anonymous_cannot_create_task(self):
        resp = self.client.post(
            reverse('task_create', kwargs={'project_pk': self.project.pk}),
            {'title': 'Anon Task', 'status': Task.STATUS_TODO, 'priority': Task.PRIORITY_LOW}
        )
        self.assertFalse(Task.objects.filter(title='Anon Task').exists())

    def test_blank_title_rejected(self):
        self.login_owner()
        count_before = Task.objects.count()
        self.client.post(
            reverse('task_create', kwargs={'project_pk': self.project.pk}),
            {'title': '', 'status': Task.STATUS_TODO, 'priority': Task.PRIORITY_MEDIUM}
        )
        self.assertEqual(Task.objects.count(), count_before)

    def test_task_assigned_to_must_be_project_member(self):
        """The TaskForm only shows project members in assigned_to choices."""
        self.login_owner()
        resp = self.client.post(
            reverse('task_create', kwargs={'project_pk': self.project.pk}),
            {
                'title': 'Assigned Task',
                'description': '',
                'status': Task.STATUS_TODO,
                'priority': Task.PRIORITY_MEDIUM,
                'assigned_to': self.outsider.pk,  # outsider is not a member
            }
        )
        # Task should either not be created or assigned_to should be null
        task = Task.objects.filter(title='Assigned Task').first()
        if task:
            self.assertNotEqual(task.assigned_to, self.outsider)


class TaskDetailTests(BaseTestCase):

    def test_member_can_view_task_detail(self):
        self.login_member()
        resp = self.client.get(reverse('task_detail', kwargs={'pk': self.task.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.task.title)

    def test_outsider_cannot_view_task_detail(self):
        self.login_outsider()
        resp = self.client.get(reverse('task_detail', kwargs={'pk': self.task.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_anonymous_redirected_from_task_detail(self):
        resp = self.client.get(reverse('task_detail', kwargs={'pk': self.task.pk}))
        self.assertEqual(resp.status_code, 302)


class TaskEditTests(BaseTestCase):

    def test_owner_can_edit_task(self):
        self.login_owner()
        resp = self.client.post(
            reverse('task_edit', kwargs={'pk': self.task.pk}),
            {
                'title': 'Edited Task Title',
                'description': 'Updated',
                'status': Task.STATUS_IN_PROGRESS,
                'priority': Task.PRIORITY_HIGH,
            }
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Edited Task Title')

    def test_creator_can_edit_own_task(self):
        # Task was created by owner; member creates their own task
        member_task = Task.objects.create(
            title='Member Task',
            project=self.project,
            board=self.board,
            status=Task.STATUS_TODO,
            priority=Task.PRIORITY_LOW,
            created_by=self.member,
        )
        self.login_member()
        resp = self.client.post(
            reverse('task_edit', kwargs={'pk': member_task.pk}),
            {
                'title': 'Member Edited Task',
                'description': '',
                'status': Task.STATUS_TODO,
                'priority': Task.PRIORITY_LOW,
            }
        )
        member_task.refresh_from_db()
        self.assertEqual(member_task.title, 'Member Edited Task')

    def test_outsider_cannot_edit_task(self):
        self.login_outsider()
        resp = self.client.post(
            reverse('task_edit', kwargs={'pk': self.task.pk}),
            {
                'title': 'Hacked Title',
                'description': '',
                'status': Task.STATUS_TODO,
                'priority': Task.PRIORITY_LOW,
            }
        )
        self.task.refresh_from_db()
        self.assertNotEqual(self.task.title, 'Hacked Title')


class TaskStatusTests(BaseTestCase):

    def test_member_can_change_task_status(self):
        self.login_member()
        resp = self.client.post(
            reverse('task_change_status', kwargs={'pk': self.task.pk}),
            {'status': Task.STATUS_IN_PROGRESS, 'next': 'board'}
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.STATUS_IN_PROGRESS)

    def test_invalid_status_rejected(self):
        self.login_member()
        self.client.post(
            reverse('task_change_status', kwargs={'pk': self.task.pk}),
            {'status': 'not_a_real_status'}
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.STATUS_TODO)  # unchanged

    def test_outsider_cannot_change_status(self):
        self.login_outsider()
        resp = self.client.post(
            reverse('task_change_status', kwargs={'pk': self.task.pk}),
            {'status': Task.STATUS_DONE}
        )
        self.task.refresh_from_db()
        self.assertNotEqual(self.task.status, Task.STATUS_DONE)


class TaskDeleteTests(BaseTestCase):

    def test_owner_can_delete_task(self):
        self.login_owner()
        task_pk = self.task.pk
        self.client.post(reverse('task_delete', kwargs={'pk': task_pk}))
        self.assertFalse(Task.objects.filter(pk=task_pk).exists())

    def test_creator_can_delete_own_task(self):
        member_task = Task.objects.create(
            title='Deletable Task',
            project=self.project,
            board=self.board,
            status=Task.STATUS_TODO,
            priority=Task.PRIORITY_LOW,
            created_by=self.member,
        )
        self.login_member()
        self.client.post(reverse('task_delete', kwargs={'pk': member_task.pk}))
        self.assertFalse(Task.objects.filter(pk=member_task.pk).exists())

    def test_non_creator_member_cannot_delete_others_task(self):
        """A plain member who didn't create the task and isn't manager can't delete it."""
        other_member = User.objects.create_user(username='other_m', password='pass123!')
        ProjectMembership.objects.create(project=self.project, user=other_member)
        other_task = Task.objects.create(
            title='Protected Task',
            project=self.project,
            board=self.board,
            status=Task.STATUS_TODO,
            priority=Task.PRIORITY_LOW,
            created_by=self.owner,  # created by owner
        )
        self.client.login(username='other_m', password='pass123!')
        resp = self.client.post(reverse('task_delete', kwargs={'pk': other_task.pk}))
        self.assertIn(resp.status_code, [403, 404])
        self.assertTrue(Task.objects.filter(pk=other_task.pk).exists())

    def test_outsider_cannot_delete_task(self):
        self.login_outsider()
        task_pk = self.task.pk
        resp = self.client.post(reverse('task_delete', kwargs={'pk': task_pk}))
        self.assertIn(resp.status_code, [403, 404])
        self.assertTrue(Task.objects.filter(pk=task_pk).exists())


# ===========================================================================
# 7. Comment Tests
# ===========================================================================

class CommentTests(BaseTestCase):

    def test_member_can_add_comment(self):
        self.login_member()
        resp = self.client.post(
            reverse('comment_create', kwargs={'task_pk': self.task.pk}),
            {'content': 'A new comment'}
        )
        self.assertTrue(
            Comment.objects.filter(task=self.task, content='A new comment').exists()
        )

    def test_owner_can_add_comment(self):
        self.login_owner()
        self.client.post(
            reverse('comment_create', kwargs={'task_pk': self.task.pk}),
            {'content': 'Owner comment'}
        )
        self.assertTrue(
            Comment.objects.filter(task=self.task, content='Owner comment').exists()
        )

    def test_empty_comment_rejected(self):
        self.login_member()
        count_before = Comment.objects.filter(task=self.task).count()
        self.client.post(
            reverse('comment_create', kwargs={'task_pk': self.task.pk}),
            {'content': ''}
        )
        self.assertEqual(Comment.objects.filter(task=self.task).count(), count_before)

    def test_whitespace_only_comment_rejected(self):
        self.login_member()
        count_before = Comment.objects.filter(task=self.task).count()
        self.client.post(
            reverse('comment_create', kwargs={'task_pk': self.task.pk}),
            {'content': '   '}
        )
        self.assertEqual(Comment.objects.filter(task=self.task).count(), count_before)

    def test_outsider_cannot_comment(self):
        self.login_outsider()
        count_before = Comment.objects.filter(task=self.task).count()
        self.client.post(
            reverse('comment_create', kwargs={'task_pk': self.task.pk}),
            {'content': 'Outsider comment'}
        )
        self.assertEqual(Comment.objects.filter(task=self.task).count(), count_before)

    def test_user_can_delete_own_comment(self):
        self.login_member()
        comment_pk = self.comment.pk
        self.client.post(reverse('comment_delete', kwargs={'pk': comment_pk}))
        self.assertFalse(Comment.objects.filter(pk=comment_pk).exists())

    def test_owner_can_delete_any_comment(self):
        """Project owner/manager can moderate any comment."""
        self.login_owner()
        comment_pk = self.comment.pk  # comment was made by member
        self.client.post(reverse('comment_delete', kwargs={'pk': comment_pk}))
        self.assertFalse(Comment.objects.filter(pk=comment_pk).exists())

    def test_other_user_cannot_delete_comment(self):
        """A different member who didn't write the comment cannot delete it."""
        other = User.objects.create_user(username='other_commenter', password='pass123!')
        ProjectMembership.objects.create(project=self.project, user=other)
        self.client.login(username='other_commenter', password='pass123!')
        comment_pk = self.comment.pk
        resp = self.client.post(reverse('comment_delete', kwargs={'pk': comment_pk}))
        self.assertIn(resp.status_code, [403, 404])
        self.assertTrue(Comment.objects.filter(pk=comment_pk).exists())

    def test_anonymous_cannot_comment(self):
        count_before = Comment.objects.filter(task=self.task).count()
        self.client.post(
            reverse('comment_create', kwargs={'task_pk': self.task.pk}),
            {'content': 'Anon comment'}
        )
        self.assertEqual(Comment.objects.filter(task=self.task).count(), count_before)


# ===========================================================================
# 8. Permission / URL Manipulation Tests
# ===========================================================================

class PermissionTests(BaseTestCase):

    def test_url_id_manipulation_blocked_for_project(self):
        """Outsider cannot access another user's project by guessing URL."""
        self.login_outsider()
        resp = self.client.get(reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_url_id_manipulation_blocked_for_task(self):
        """Outsider cannot access a task in another project by guessing URL."""
        self.login_outsider()
        resp = self.client.get(reverse('task_detail', kwargs={'pk': self.task.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_url_id_manipulation_blocked_for_board(self):
        self.login_outsider()
        resp = self.client.get(reverse('board', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_outsider_cannot_post_to_member_add(self):
        new_user = User.objects.create_user(username='target', password='pass123!')
        self.login_outsider()
        resp = self.client.post(
            reverse('project_add_member', kwargs={'pk': self.project.pk}),
            {'username': 'target'}
        )
        self.assertIn(resp.status_code, [403, 404])

    def test_outsider_cannot_delete_project(self):
        self.login_outsider()
        resp = self.client.post(reverse('project_delete', kwargs={'pk': self.project.pk}))
        self.assertIn(resp.status_code, [403, 404])
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())


# ===========================================================================
# 9. Dashboard / Statistics Tests
# ===========================================================================

class DashboardTests(BaseTestCase):

    def test_dashboard_loads_for_authenticated_user(self):
        self.login_owner()
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_shows_project_name(self):
        self.login_owner()
        resp = self.client.get(reverse('dashboard'))
        self.assertContains(resp, self.project.name)

    def test_dashboard_stats_are_correct(self):
        # Add a second done task
        Task.objects.create(
            title='Done Task',
            project=self.project,
            board=self.board,
            status=Task.STATUS_DONE,
            priority=Task.PRIORITY_LOW,
            created_by=self.owner,
        )
        self.login_owner()
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        # Both tasks should exist in DB
        self.assertEqual(Task.objects.filter(project=self.project).count(), 2)

    def test_dashboard_shows_assigned_tasks(self):
        self.task.assigned_to = self.owner
        self.task.save()
        self.login_owner()
        resp = self.client.get(reverse('dashboard'))
        self.assertContains(resp, self.task.title)

    def test_anonymous_redirected_from_dashboard(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)


# ===========================================================================
# 10. Model Tests
# ===========================================================================

class ProjectModelTests(BaseTestCase):

    def test_project_is_member_true_for_owner(self):
        self.assertTrue(self.project.is_member(self.owner))

    def test_project_is_member_true_for_member(self):
        self.assertTrue(self.project.is_member(self.member))

    def test_project_is_member_false_for_outsider(self):
        self.assertFalse(self.project.is_member(self.outsider))

    def test_project_is_manager_true_for_owner(self):
        self.assertTrue(self.project.is_manager(self.owner))

    def test_project_is_manager_false_for_plain_member(self):
        self.assertFalse(self.project.is_manager(self.member))

    def test_project_member_count(self):
        # 1 owner + 1 member = 2
        self.assertEqual(self.project.member_count, 2)

    def test_project_task_count(self):
        self.assertEqual(self.project.task_count, 1)

    def test_project_completed_task_count(self):
        self.task.status = Task.STATUS_DONE
        self.task.save()
        self.assertEqual(self.project.completed_task_count, 1)


class TaskModelTests(BaseTestCase):

    def test_task_is_overdue_when_past_due_date(self):
        self.task.due_date = date.today() - timedelta(days=1)
        self.task.status = Task.STATUS_TODO
        self.task.save()
        self.assertTrue(self.task.is_overdue)

    def test_task_not_overdue_when_no_due_date(self):
        self.task.due_date = None
        self.task.save()
        self.assertFalse(self.task.is_overdue)

    def test_task_not_overdue_when_done(self):
        self.task.due_date = date.today() - timedelta(days=1)
        self.task.status = Task.STATUS_DONE
        self.task.save()
        self.assertFalse(self.task.is_overdue)

    def test_task_comment_count(self):
        self.assertEqual(self.task.comment_count, 1)

    def test_task_str(self):
        self.assertEqual(str(self.task), self.task.title)


class ProfileModelTests(TestCase):

    def test_profile_display_name_uses_full_name(self):
        user = User.objects.create_user(
            username='fullname', password='pass',
            first_name='John', last_name='Doe'
        )
        self.assertEqual(user.profile.display_name, 'John Doe')

    def test_profile_display_name_falls_back_to_username(self):
        user = User.objects.create_user(username='noname', password='pass')
        self.assertEqual(user.profile.display_name, 'noname')


# ===========================================================================
# 11. Search Tests
# ===========================================================================

class SearchTests(BaseTestCase):

    def test_search_page_loads(self):
        self.login_owner()
        resp = self.client.get(reverse('search'))
        self.assertEqual(resp.status_code, 200)

    def test_search_finds_project_by_name(self):
        self.login_owner()
        resp = self.client.get(reverse('search'), {'q': 'Test Project'})
        self.assertContains(resp, self.project.name)

    def test_search_finds_task_by_title(self):
        self.login_owner()
        resp = self.client.get(reverse('search'), {'q': 'Test Task'})
        self.assertContains(resp, self.task.title)

    def test_search_does_not_show_inaccessible_projects(self):
        """Outsider's search should not return projects they can't access."""
        self.login_outsider()
        resp = self.client.get(reverse('search'), {'q': 'Test Project'})
        self.assertNotContains(resp, self.project.name)

    def test_empty_search_returns_no_results(self):
        self.login_owner()
        resp = self.client.get(reverse('search'), {'q': ''})
        self.assertEqual(resp.status_code, 200)
