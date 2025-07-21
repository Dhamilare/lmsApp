from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import *
from .models import *

def is_admin(user):
    return user.is_authenticated and user.is_staff

def is_instructor(user):
    return user.is_authenticated and user.is_instructor

def is_student(user):
    return user.is_authenticated and user.is_student

def student_register(request):
    """
    Handles student registration.
    Only allows students to register.
    """
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log in the user after successful registration
            messages.success(request, 'Registration successful! Welcome to LMS Portal.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    """
    Handles user login for all roles (Admin, Instructor, Student).
    """
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    """
    Logs out the current user.
    """
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def dashboard(request):
    """
    Displays the user's dashboard based on their role.
    """
    user = request.user
    context = {
        'user': user,
        'is_admin': user.is_staff,
        'is_instructor': user.is_instructor,
        'is_student': user.is_student,
    }

    if user.is_instructor:
        context['courses'] = Course.objects.filter(instructor=user).order_by('-created_at')
    elif user.is_student:
        # For students, we'll later add enrolled courses
        context['available_courses'] = Course.objects.filter(is_published=True).order_by('-created_at')[:5] # Show some available courses
    
    return render(request, 'dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def create_instructor(request):
    """
    Allows an Admin to create a new Instructor account.
    """
    if request.method == 'POST':
        form = InstructorCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Instructor {user.username} created successfully!')
            return redirect('dashboard') # Or redirect to an admin user management page
        else:
            messages.error(request, 'Failed to create instructor. Please correct the errors.')
    else:
        form = InstructorCreationForm()
    return render(request, 'admin/create_instructor.html', {'form': form})

@login_required
@user_passes_test(is_instructor)
def course_list(request):
    """
    Lists courses managed by the logged-in instructor.
    """
    courses = Course.objects.filter(instructor=request.user).order_by('-created_at')
    return render(request, 'instructor/course_list.html', {'courses': courses})

@login_required
@user_passes_test(is_instructor)
def course_create(request):
    """
    Allows an instructor to create a new course.
    """
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, f'Course "{course.title}" created successfully!')
            return redirect('course_detail', slug=course.slug)
        else:
            messages.error(request, 'Failed to create course. Please correct the errors.')
    else:
        form = CourseForm()
    return render(request, 'instructor/course_form.html', {'form': form, 'page_title': 'Create New Course'})

@login_required
@user_passes_test(is_instructor)
def course_update(request, slug): 
    """
    Allows an instructor to update an existing course.
    Ensures the instructor owns the course.
    """
    course = get_object_or_404(Course, slug=slug, instructor=request.user)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course "{course.title}" updated successfully!')
            return redirect('course_detail', slug=course.slug)
        else:
            messages.error(request, 'Failed to update course. Please correct the errors.')
    else:
        form = CourseForm(instance=course)
    return render(request, 'instructor/course_form.html', {'form': form, 'page_title': f'Edit Course: {course.title}'})

@login_required
def course_detail(request, slug):
    """
    Displays the details of a specific course.
    Access control will be implemented later for enrollment/paid courses.
    For now, instructors can view their own courses, students can view published courses.
    """
    course = get_object_or_404(Course, slug=slug) 

    # Basic access control for now
    if request.user.is_instructor and course.instructor != request.user:
        messages.error(request, "You do not have permission to view this course.")
        return redirect('dashboard') # Or a more appropriate redirect

    if request.user.is_student and not course.is_published:
        messages.error(request, "This course is not yet published.")
        return redirect('dashboard') # Or a more appropriate redirect

    return render(request, 'instrctor/course_detail.html', {'course': course})
