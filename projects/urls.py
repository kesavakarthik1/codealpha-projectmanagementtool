from django.urls import path
from . import views

urlpatterns = [

    # -----------------------------------------------------------------------
    # Home
    # -----------------------------------------------------------------------
    path('', views.home, name='home'),

    # -----------------------------------------------------------------------
    # Authentication
    # -----------------------------------------------------------------------
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # -----------------------------------------------------------------------
    # Dashboard & Search
    # -----------------------------------------------------------------------
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.search_view, name='search'),

    # -----------------------------------------------------------------------
    # Profile
    # -----------------------------------------------------------------------
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='user_profile'),

    # -----------------------------------------------------------------------
    # Projects
    # -----------------------------------------------------------------------
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),

    # -----------------------------------------------------------------------
    # Project Members
    # -----------------------------------------------------------------------
    path('projects/<int:pk>/members/', views.project_members, name='project_members'),
    path('projects/<int:pk>/members/add/', views.project_add_member, name='project_add_member'),
    path('projects/<int:pk>/members/<int:user_id>/remove/', views.project_remove_member, name='project_remove_member'),
    path('projects/<int:pk>/members/<int:user_id>/role/', views.project_change_member_role, name='project_change_member_role'),

    # -----------------------------------------------------------------------
    # Board
    # -----------------------------------------------------------------------
    path('projects/<int:pk>/board/', views.board_view, name='board'),

    # -----------------------------------------------------------------------
    # Tasks
    # -----------------------------------------------------------------------
    path('projects/<int:project_pk>/tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:pk>/status/', views.task_change_status, name='task_change_status'),

    # -----------------------------------------------------------------------
    # Comments
    # -----------------------------------------------------------------------
    path('tasks/<int:task_pk>/comments/add/', views.comment_create, name='comment_create'),
    path('comments/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
]
