"""
Management command: seed_data
Creates realistic sample data for the ProjectFlow application.

Usage:
    python manage.py seed_data           # create data (skips if already exists)
    python manage.py seed_data --flush   # delete all app data first, then reseed
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
import random

from projects.models import (
    Profile, Project, ProjectMembership, Board, Task, Comment
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _future(days):
    return date.today() + timedelta(days=days)

def _past(days):
    return date.today() - timedelta(days=days)


class Command(BaseCommand):
    help = 'Seed the database with realistic sample data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing app data before seeding.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing existing app data…'))
            Comment.objects.all().delete()
            Task.objects.all().delete()
            Board.objects.all().delete()
            ProjectMembership.objects.all().delete()
            Project.objects.all().delete()
            Profile.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Existing data removed.'))

        # ----------------------------------------------------------------
        # 1. Users
        # ----------------------------------------------------------------
        self.stdout.write('Creating users…')

        users_data = [
            {
                'username': 'alice_dev',
                'email': 'alice@projectflow.dev',
                'first_name': 'Alice',
                'last_name': 'Morgan',
                'password': 'Demo1234!',
                'bio': 'Full-stack developer with 5 years experience. Loves Python and clean code.',
            },
            {
                'username': 'bob_design',
                'email': 'bob@projectflow.dev',
                'first_name': 'Bob',
                'last_name': 'Chen',
                'password': 'Demo1234!',
                'bio': 'UI/UX designer focused on accessible, user-friendly interfaces.',
            },
            {
                'username': 'carol_pm',
                'email': 'carol@projectflow.dev',
                'first_name': 'Carol',
                'last_name': 'Singh',
                'password': 'Demo1234!',
                'bio': 'Project manager with Agile certification. Expert at keeping teams on track.',
            },
            {
                'username': 'dave_backend',
                'email': 'dave@projectflow.dev',
                'first_name': 'Dave',
                'last_name': 'Okonkwo',
                'password': 'Demo1234!',
                'bio': 'Backend engineer specialising in Django, PostgreSQL, and REST APIs.',
            },
            {
                'username': 'eva_qa',
                'email': 'eva@projectflow.dev',
                'first_name': 'Eva',
                'last_name': 'Martinez',
                'password': 'Demo1234!',
                'bio': 'QA engineer and automation specialist. Writes tests so bugs don\'t slip through.',
            },
            {
                'username': 'frank_devops',
                'email': 'frank@projectflow.dev',
                'first_name': 'Frank',
                'last_name': 'Williams',
                'password': 'Demo1234!',
                'bio': 'DevOps engineer. Docker, Kubernetes, CI/CD pipelines are my playground.',
            },
        ]

        users = {}
        for ud in users_data:
            user, created = User.objects.get_or_create(
                username=ud['username'],
                defaults={
                    'email': ud['email'],
                    'first_name': ud['first_name'],
                    'last_name': ud['last_name'],
                }
            )
            if created:
                user.set_password(ud['password'])
                user.save()
                self.stdout.write(f"  Created user: {user.username}")
            else:
                self.stdout.write(f"  Skipped existing user: {user.username}")

            # Ensure profile exists and has bio
            profile, _ = Profile.objects.get_or_create(user=user)
            if not profile.bio:
                profile.bio = ud['bio']
                profile.save()

            users[ud['username']] = user

        alice  = users['alice_dev']
        bob    = users['bob_design']
        carol  = users['carol_pm']
        dave   = users['dave_backend']
        eva    = users['eva_qa']
        frank  = users['frank_devops']

        # ----------------------------------------------------------------
        # 2. Projects
        # ----------------------------------------------------------------
        self.stdout.write('Creating projects…')

        projects_data = [
            {
                'name': 'E-Commerce Platform Redesign',
                'description': (
                    'A complete overhaul of the customer-facing e-commerce website. '
                    'Goals include improved mobile performance, modernised UI, '
                    'streamlined checkout flow, and better accessibility compliance.'
                ),
                'owner': alice,
                'status': Project.STATUS_ACTIVE,
                'members': [bob, carol, dave, eva],
                'member_roles': {
                    bob.username: ProjectMembership.ROLE_MEMBER,
                    carol.username: ProjectMembership.ROLE_MANAGER,
                    dave.username: ProjectMembership.ROLE_MEMBER,
                    eva.username: ProjectMembership.ROLE_MEMBER,
                },
            },
            {
                'name': 'Mobile App – iOS & Android',
                'description': (
                    'Build the first version of our cross-platform mobile application. '
                    'Core features: user authentication, push notifications, '
                    'offline mode, and integration with the main API.'
                ),
                'owner': carol,
                'status': Project.STATUS_ACTIVE,
                'members': [alice, bob, frank],
                'member_roles': {
                    alice.username: ProjectMembership.ROLE_MANAGER,
                    bob.username: ProjectMembership.ROLE_MEMBER,
                    frank.username: ProjectMembership.ROLE_MEMBER,
                },
            },
            {
                'name': 'Infrastructure Migration',
                'description': (
                    'Migrate all services from legacy bare-metal servers to a '
                    'containerised Kubernetes cluster on AWS. Includes CI/CD '
                    'pipeline setup, monitoring, and zero-downtime deployment strategy.'
                ),
                'owner': frank,
                'status': Project.STATUS_ACTIVE,
                'members': [alice, dave, eva],
                'member_roles': {
                    alice.username: ProjectMembership.ROLE_MEMBER,
                    dave.username: ProjectMembership.ROLE_MANAGER,
                    eva.username: ProjectMembership.ROLE_MEMBER,
                },
            },
            {
                'name': 'Internal HR Portal',
                'description': (
                    'An internal web application for HR processes: employee onboarding, '
                    'leave requests, performance reviews, and org-chart visualisation.'
                ),
                'owner': carol,
                'status': Project.STATUS_ON_HOLD,
                'members': [alice, bob],
                'member_roles': {
                    alice.username: ProjectMembership.ROLE_MEMBER,
                    bob.username: ProjectMembership.ROLE_MEMBER,
                },
            },
        ]

        projects = {}
        for pd in projects_data:
            project, created = Project.objects.get_or_create(
                name=pd['name'],
                defaults={
                    'description': pd['description'],
                    'owner': pd['owner'],
                    'status': pd['status'],
                }
            )
            if created:
                self.stdout.write(f"  Created project: {project.name}")
            else:
                self.stdout.write(f"  Skipped existing project: {project.name}")

            # Ensure board exists (signal handles this for new projects)
            Board.objects.get_or_create(project=project, defaults={'name': 'Main Board'})

            # Add members
            for member in pd['members']:
                role = pd['member_roles'].get(member.username, ProjectMembership.ROLE_MEMBER)
                ProjectMembership.objects.get_or_create(
                    project=project,
                    user=member,
                    defaults={'role': role},
                )

            projects[pd['name']] = project

        ecom   = projects['E-Commerce Platform Redesign']
        mobile = projects['Mobile App – iOS & Android']
        infra  = projects['Infrastructure Migration']
        hr     = projects['Internal HR Portal']

        ecom_board   = Board.objects.get(project=ecom)
        mobile_board = Board.objects.get(project=mobile)
        infra_board  = Board.objects.get(project=infra)
        hr_board     = Board.objects.get(project=hr)

        # ----------------------------------------------------------------
        # 3. Tasks
        # ----------------------------------------------------------------
        self.stdout.write('Creating tasks…')

        tasks_data = [
            # ---- E-Commerce ----
            {
                'title': 'Audit current site accessibility',
                'description': 'Run WCAG 2.1 AA audit using axe and manual keyboard testing. Document all issues in a spreadsheet with severity ratings.',
                'project': ecom, 'board': ecom_board,
                'status': Task.STATUS_DONE, 'priority': Task.PRIORITY_HIGH,
                'assigned_to': eva, 'created_by': alice,
                'due_date': _past(10),
            },
            {
                'title': 'Design new homepage mockups',
                'description': 'Create 3 homepage design concepts in Figma. Focus on hero section, featured products grid, and trust signals.',
                'project': ecom, 'board': ecom_board,
                'status': Task.STATUS_DONE, 'priority': Task.PRIORITY_HIGH,
                'assigned_to': bob, 'created_by': alice,
                'due_date': _past(5),
            },
            {
                'title': 'Implement responsive product grid',
                'description': 'Convert the product listing page from a fixed-width layout to a responsive CSS grid. Must work from 320px to 2560px.',
                'project': ecom, 'board': ecom_board,
                'status': Task.STATUS_IN_PROGRESS, 'priority': Task.PRIORITY_HIGH,
                'assigned_to': dave, 'created_by': alice,
                'due_date': _future(7),
            },
            {
                'title': 'Optimise checkout flow',
                'description': 'Reduce checkout from 5 steps to 3. Implement address autocomplete, saved payment methods, and guest checkout.',
                'project': ecom, 'board': ecom_board,
                'status': Task.STATUS_IN_PROGRESS, 'priority': Task.PRIORITY_URGENT,
                'assigned_to': dave, 'created_by': carol,
                'due_date': _future(14),
            },
            {
                'title': 'Write end-to-end checkout tests',
                'description': 'Using Playwright, write E2E tests covering: add to cart, guest checkout, logged-in checkout, payment failure scenarios.',
                'project': ecom, 'board': ecom_board,
                'status': Task.STATUS_TODO, 'priority': Task.PRIORITY_MEDIUM,
                'assigned_to': eva, 'created_by': alice,
                'due_date': _future(21),
            },
            {
                'title': 'Performance: image optimisation pipeline',
                'description': 'Set up automatic WebP conversion and lazy loading for all product images. Target: LCP under 2.5s on mobile.',
                'project': ecom, 'board': ecom_board,
                'status': Task.STATUS_REVIEW, 'priority': Task.PRIORITY_MEDIUM,
                'assigned_to': alice, 'created_by': alice,
                'due_date': _future(3),
            },
            {
                'title': 'Update component design tokens',
                'description': 'Replace all hard-coded colours, spacing, and typography values with CSS custom properties from the new design system.',
                'project': ecom, 'board': ecom_board,
                'status': Task.STATUS_TODO, 'priority': Task.PRIORITY_LOW,
                'assigned_to': bob, 'created_by': bob,
                'due_date': _future(30),
            },

            # ---- Mobile App ----
            {
                'title': 'Set up React Native project structure',
                'description': 'Initialise the React Native project with TypeScript, ESLint, Prettier, and folder structure conventions. Configure Metro bundler.',
                'project': mobile, 'board': mobile_board,
                'status': Task.STATUS_DONE, 'priority': Task.PRIORITY_HIGH,
                'assigned_to': alice, 'created_by': carol,
                'due_date': _past(20),
            },
            {
                'title': 'Design onboarding screens',
                'description': 'Create designs for the 4-screen onboarding flow: welcome, feature highlights, permissions request, and profile setup.',
                'project': mobile, 'board': mobile_board,
                'status': Task.STATUS_DONE, 'priority': Task.PRIORITY_MEDIUM,
                'assigned_to': bob, 'created_by': carol,
                'due_date': _past(15),
            },
            {
                'title': 'Implement push notification service',
                'description': 'Integrate Firebase Cloud Messaging for iOS and Android. Handle foreground, background, and killed state notifications.',
                'project': mobile, 'board': mobile_board,
                'status': Task.STATUS_IN_PROGRESS, 'priority': Task.PRIORITY_HIGH,
                'assigned_to': frank, 'created_by': carol,
                'due_date': _future(10),
            },
            {
                'title': 'Offline mode: local data sync',
                'description': 'Implement SQLite local storage with sync queue. Handle conflict resolution when reconnecting after offline period.',
                'project': mobile, 'board': mobile_board,
                'status': Task.STATUS_TODO, 'priority': Task.PRIORITY_HIGH,
                'assigned_to': alice, 'created_by': carol,
                'due_date': _future(25),
            },
            {
                'title': 'App Store and Play Store submission prep',
                'description': 'Prepare store assets: app icons (all sizes), screenshots, descriptions, privacy policy. Submit for review.',
                'project': mobile, 'board': mobile_board,
                'status': Task.STATUS_TODO, 'priority': Task.PRIORITY_MEDIUM,
                'assigned_to': bob, 'created_by': carol,
                'due_date': _future(45),
            },
            {
                'title': 'Authentication: JWT token refresh',
                'description': 'Implement silent token refresh using refresh tokens stored in Keychain (iOS) and Keystore (Android).',
                'project': mobile, 'board': mobile_board,
                'status': Task.STATUS_REVIEW, 'priority': Task.PRIORITY_URGENT,
                'assigned_to': alice, 'created_by': alice,
                'due_date': _future(2),
            },

            # ---- Infrastructure ----
            {
                'title': 'Dockerise all microservices',
                'description': 'Write optimised multi-stage Dockerfiles for each service. Ensure images run as non-root and pass Trivy security scan.',
                'project': infra, 'board': infra_board,
                'status': Task.STATUS_DONE, 'priority': Task.PRIORITY_URGENT,
                'assigned_to': frank, 'created_by': frank,
                'due_date': _past(30),
            },
            {
                'title': 'Set up Kubernetes cluster on AWS EKS',
                'description': 'Provision EKS cluster with Terraform. Configure node groups, IAM roles, VPC networking, and security groups.',
                'project': infra, 'board': infra_board,
                'status': Task.STATUS_IN_PROGRESS, 'priority': Task.PRIORITY_URGENT,
                'assigned_to': frank, 'created_by': frank,
                'due_date': _future(12),
            },
            {
                'title': 'Configure GitHub Actions CI/CD pipeline',
                'description': 'Set up workflows for: lint, test, build, push to ECR, deploy to staging, manual promotion to production.',
                'project': infra, 'board': infra_board,
                'status': Task.STATUS_IN_PROGRESS, 'priority': Task.PRIORITY_HIGH,
                'assigned_to': dave, 'created_by': frank,
                'due_date': _future(8),
            },
            {
                'title': 'Set up Prometheus + Grafana monitoring',
                'description': 'Deploy Prometheus with kube-state-metrics and node-exporter. Build Grafana dashboards for key SLIs. Configure PagerDuty alerts.',
                'project': infra, 'board': infra_board,
                'status': Task.STATUS_TODO, 'priority': Task.PRIORITY_HIGH,
                'assigned_to': frank, 'created_by': frank,
                'due_date': _future(20),
            },
            {
                'title': 'Database migration: RDS PostgreSQL',
                'description': 'Migrate from self-hosted MySQL to AWS RDS PostgreSQL. Includes schema conversion, data migration, and cutover plan.',
                'project': infra, 'board': infra_board,
                'status': Task.STATUS_TODO, 'priority': Task.PRIORITY_MEDIUM,
                'assigned_to': dave, 'created_by': frank,
                'due_date': _future(35),
            },

            # ---- HR Portal ----
            {
                'title': 'Define HR portal requirements',
                'description': 'Gather requirements from HR team. Document user stories, data model, integration points with existing payroll system.',
                'project': hr, 'board': hr_board,
                'status': Task.STATUS_DONE, 'priority': Task.PRIORITY_HIGH,
                'assigned_to': carol, 'created_by': carol,
                'due_date': _past(45),
            },
            {
                'title': 'Design employee dashboard wireframes',
                'description': 'Wireframes for: employee profile, leave balance widget, upcoming reviews, team org chart. Present to stakeholders.',
                'project': hr, 'board': hr_board,
                'status': Task.STATUS_REVIEW, 'priority': Task.PRIORITY_MEDIUM,
                'assigned_to': bob, 'created_by': carol,
                'due_date': _past(5),
            },
        ]

        created_tasks = {}
        for td in tasks_data:
            task, created = Task.objects.get_or_create(
                title=td['title'],
                project=td['project'],
                defaults={
                    'description': td['description'],
                    'board': td['board'],
                    'status': td['status'],
                    'priority': td['priority'],
                    'assigned_to': td['assigned_to'],
                    'created_by': td['created_by'],
                    'due_date': td['due_date'],
                }
            )
            if created:
                self.stdout.write(f"  Created task: {task.title}")
            else:
                self.stdout.write(f"  Skipped existing task: {task.title}")
            created_tasks[td['title']] = task

        # ----------------------------------------------------------------
        # 4. Comments
        # ----------------------------------------------------------------
        self.stdout.write('Creating comments…')

        comments_data = [
            # Checkout flow
            {
                'task': created_tasks['Optimise checkout flow'],
                'author': carol,
                'content': 'This is top priority for Q1. The current 5-step checkout is killing our conversion rate — analytics show a 68% drop-off at the payment screen.',
            },
            {
                'task': created_tasks['Optimise checkout flow'],
                'author': dave,
                'content': 'I\'ve started on the address autocomplete using the Google Places API. Guest checkout should be straightforward. The saved payment methods will need a tokenisation service — should we use Stripe or build our own?',
            },
            {
                'task': created_tasks['Optimise checkout flow'],
                'author': alice,
                'content': 'Definitely Stripe — PCI compliance alone makes rolling our own a non-starter. I\'ll set up the Stripe integration this week.',
            },
            {
                'task': created_tasks['Optimise checkout flow'],
                'author': eva,
                'content': 'I\'ll need a staging environment with test card details once the Stripe integration is up. Can you add me to the Stripe test account?',
            },

            # Product grid
            {
                'task': created_tasks['Implement responsive product grid'],
                'author': dave,
                'content': 'Grid is working well on desktop and tablet. Finding some issues with the filter sidebar collapsing incorrectly on 375px width. Will fix today.',
            },
            {
                'task': created_tasks['Implement responsive product grid'],
                'author': bob,
                'content': 'I noticed the card hover state doesn\'t work on touch devices — that\'s expected, but we should make sure the tap target is at least 44x44px. Accessibility requirement.',
            },
            {
                'task': created_tasks['Implement responsive product grid'],
                'author': dave,
                'content': 'Good catch Bob. Updated touch targets to 48x48px to give some breathing room. Also fixed the sidebar issue — it was a missing media query breakpoint.',
            },

            # Image optimisation
            {
                'task': created_tasks['Performance: image optimisation pipeline'],
                'author': alice,
                'content': 'Pipeline is set up using Sharp in the build process. WebP conversion is working and the lazy loading polyfill handles Safari 11. LCP is now averaging 1.9s on mobile — down from 4.2s.',
            },
            {
                'task': created_tasks['Performance: image optimisation pipeline'],
                'author': eva,
                'content': 'Verified in Chrome DevTools and Lighthouse. Score jumped from 42 to 87 on mobile performance. Marking as ready for review.',
            },
            {
                'task': created_tasks['Performance: image optimisation pipeline'],
                'author': carol,
                'content': 'Excellent work. Can we get a quick demo for the stakeholder call on Thursday?',
            },

            # Push notifications
            {
                'task': created_tasks['Implement push notification service'],
                'author': frank,
                'content': 'FCM integration is done for Android. iOS requires APNs certificate setup — I\'ve raised a ticket with IT to get the Apple Developer account sorted.',
            },
            {
                'task': created_tasks['Implement push notification service'],
                'author': carol,
                'content': 'Apple Developer account access has been arranged — Frank, you should get an invite shortly. Deadline on this is firm — we need notifications for the beta launch.',
            },

            # Kubernetes
            {
                'task': created_tasks['Set up Kubernetes cluster on AWS EKS'],
                'author': frank,
                'content': 'Node groups are provisioned. Struggling with the VPC CNI plugin — there\'s a known issue with the latest version. Using v1.11.4 as a workaround for now.',
            },
            {
                'task': created_tasks['Set up Kubernetes cluster on AWS EKS'],
                'author': dave,
                'content': 'I hit the same CNI issue last year. The workaround is fine for now. Also, don\'t forget to enable cluster autoscaler — we\'ll need it for the traffic spikes.',
            },
            {
                'task': created_tasks['Set up Kubernetes cluster on AWS EKS'],
                'author': frank,
                'content': 'Autoscaler configured with min=2, max=10 nodes per group. Also set up Karpenter as a secondary option for burst capacity.',
            },

            # CI/CD
            {
                'task': created_tasks['Configure GitHub Actions CI/CD pipeline'],
                'author': dave,
                'content': 'Lint and test stages are running. Build and push to ECR is working. Working on the staging deployment job now — need to configure kubectl credentials securely.',
            },
            {
                'task': created_tasks['Configure GitHub Actions CI/CD pipeline'],
                'author': frank,
                'content': 'Use OIDC authentication for the kubectl credentials — don\'t use long-lived access keys. I\'ve set up the IAM OIDC provider already. The workflow role ARN is in our secrets.',
            },

            # JWT
            {
                'task': created_tasks['Authentication: JWT token refresh'],
                'author': alice,
                'content': 'Silent refresh is implemented. iOS Keychain works perfectly. Android Keystore required some extra handling for API levels below 23 but it\'s sorted now.',
            },
            {
                'task': created_tasks['Authentication: JWT token refresh'],
                'author': carol,
                'content': 'This is blocking the beta release. Please prioritise the review — I need two approvals before we can merge.',
            },

            # HR wireframes
            {
                'task': created_tasks['Design employee dashboard wireframes'],
                'author': bob,
                'content': 'Wireframes are complete and in the Figma file. I\'ve done 3 variations of the leave balance widget — let me know which direction you prefer before I move to high-fidelity.',
            },
            {
                'task': created_tasks['Design employee dashboard wireframes'],
                'author': carol,
                'content': 'I like variation 2 — it\'s the most compact and works better on smaller screens. Can we get HR\'s sign-off before Thursday?',
            },
        ]

        for cd in comments_data:
            # Avoid duplicating comments (check by task + author + first 50 chars)
            snippet = cd['content'][:50]
            exists = Comment.objects.filter(
                task=cd['task'],
                author=cd['author'],
                content__startswith=snippet,
            ).exists()
            if not exists:
                Comment.objects.create(
                    task=cd['task'],
                    author=cd['author'],
                    content=cd['content'],
                )
                self.stdout.write(f"  Created comment by {cd['author'].username} on '{cd['task'].title}'")
            else:
                self.stdout.write(f"  Skipped existing comment by {cd['author'].username}")

        # ----------------------------------------------------------------
        # Summary
        # ----------------------------------------------------------------
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Seed data complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f"  Users:    {User.objects.filter(is_superuser=False).count()}")
        self.stdout.write(f"  Projects: {Project.objects.count()}")
        self.stdout.write(f"  Boards:   {Board.objects.count()}")
        self.stdout.write(f"  Tasks:    {Task.objects.count()}")
        self.stdout.write(f"  Comments: {Comment.objects.count()}")
        self.stdout.write('')
        self.stdout.write('Demo login credentials (password: Demo1234!):')
        self.stdout.write('  alice_dev  – project owner (E-Commerce)')
        self.stdout.write('  carol_pm   – project owner (Mobile App, HR Portal)')
        self.stdout.write('  frank_devops – project owner (Infrastructure)')
        self.stdout.write('  bob_design, dave_backend, eva_qa – team members')
        self.stdout.write('')
        self.stdout.write('To create a superuser for Django admin:')
        self.stdout.write('  python manage.py createsuperuser')
