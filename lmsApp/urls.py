from django.urls import path
from . import views

urlpatterns = [
    path('accounts/register/', views.student_register, name='register'),
    path('accounts/login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('admin/create-instructor/', views.create_instructor, name='create_instructor'), # Admin only
    path('courses/', views.course_list, name='course_list'), # Instructor only
    path('courses/create/', views.course_create, name='course_create'), # Instructor only
    path('courses/<slug:slug>/edit/', views.course_update, name='course_update'), # Instructor only
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'), # All roles with access control
]
