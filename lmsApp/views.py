# instructor/views.py (Updated for AJAX Modals)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.template.loader import render_to_string

from .forms import *
from .models import *

# Helper functions for role-based access control
def is_admin(user):
    return user.is_authenticated and user.is_staff

def is_instructor(user):
    return user.is_authenticated and user.is_instructor

def is_student(user):
    return user.is_authenticated and user.is_student

def is_ajax(request):
    """Helper to check if a request is an AJAX request."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

# --- Authentication and Dashboard Views ---

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

# --- Admin Functionality ---

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
@user_passes_test(is_admin)
def instructor_list(request):
    """
    Admin view to list all instructors.
    """
    instructors = User.objects.filter(is_instructor=True).order_by('username')
    return render(request, 'admin/instructor_list.html', {'instructors': instructors})

@login_required
@user_passes_test(is_admin)
def instructor_update(request, pk):
    """
    Admin view to update an instructor's details.
    """
    instructor = get_object_or_404(User, pk=pk, is_instructor=True)
    template_name = 'admin/_instructor_form.html' if is_ajax(request) else 'core/instructor_form.html'

    if request.method == 'POST':
        form = InstructorUpdateForm(request.POST, instance=instructor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Instructor "{instructor.username}" updated successfully!')
            if is_ajax(request):
                return JsonResponse({'success': True, 'message': f'Instructor "{instructor.username}" updated successfully!'})
            return redirect('instructor_list')
        else:
            if is_ajax(request):
                form_html = render_to_string(template_name, {'form': form, 'instructor': instructor, 'page_title': f'Edit Instructor: {instructor.username}'}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html, 'error': 'Validation failed.'})
            messages.error(request, 'Failed to update instructor. Please correct the errors.')
    else:
        form = InstructorUpdateForm(instance=instructor)
    return render(request, template_name, {'form': form, 'instructor': instructor, 'page_title': f'Edit Instructor: {instructor.username}'})

@login_required
@user_passes_test(is_admin)
def instructor_delete(request, pk):
    """
    Admin view to delete an instructor.
    """
    instructor = get_object_or_404(User, pk=pk, is_instructor=True)
    template_name = 'admin/_confirm_delete.html' if is_ajax(request) else 'core/confirm_delete.html'

    if request.method == 'POST':
        if instructor == request.user: # Prevent admin from deleting themselves
            messages.error(request, "You cannot delete your own account.")
            if is_ajax(request):
                return JsonResponse({'success': False, 'error': "You cannot delete your own account."})
            return redirect('instructor_list')
        
        instructor.delete()
        messages.success(request, f'Instructor "{instructor.username}" deleted successfully.')
        if is_ajax(request):
            return JsonResponse({'success': True, 'message': f'Instructor "{instructor.username}" deleted successfully!', 'redirect_url': str(redirect('instructor_list').url)})
        return redirect('instructor_list')
    
    context = {'object': instructor, 'type': 'instructor'}
    if is_ajax(request):
        return render(request, template_name, context)
    return render(request, template_name, context)

# --- Instructor Course Management ---

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
    template_name = 'instructor/_course_form.html' if is_ajax(request) else 'instructor/course_form.html'

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, f'Course "{course.title}" created successfully!')
            if is_ajax(request):
                return JsonResponse({'success': True, 'message': f'Course "{course.title}" created successfully!', 'redirect_url': str(course.get_absolute_url())}) # Assuming get_absolute_url
            return redirect('course_detail', slug=course.slug)
        else:
            if is_ajax(request):
                form_html = render_to_string(template_name, {'form': form, 'page_title': 'Create New Course'}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html, 'error': 'Validation failed.'})
            messages.error(request, 'Failed to create course. Please correct the errors.')
    else:
        form = CourseForm()
    return render(request, template_name, {'form': form, 'page_title': 'Create New Course'})


@login_required
@user_passes_test(is_instructor)
def course_update(request, slug):
    """
    Allows an instructor to update an existing course.
    Ensures the instructor owns the course.
    """
    course = get_object_or_404(Course, slug=slug, instructor=request.user)
    template_name = 'instructor/_course_form.html' if is_ajax(request) else 'instructor/course_form.html'

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course "{course.title}" updated successfully!')
            if is_ajax(request):
                return JsonResponse({'success': True, 'message': f'Course "{course.title}" updated successfully!'})
            return redirect('course_detail', slug=course.slug)
        else:
            if is_ajax(request):
                form_html = render_to_string(template_name, {'form': form, 'page_title': f'Edit Course: {course.title}', 'course': course}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html, 'error': 'Validation failed.'})
            messages.error(request, 'Failed to update course. Please correct the errors.')
    else:
        form = CourseForm(instance=course)
    return render(request, template_name, {'form': form, 'page_title': f'Edit Course: {course.title}', 'course': course})

@login_required
@user_passes_test(is_instructor)
def course_delete(request, slug):
    """
    Allows an instructor to delete a course.
    """
    course = get_object_or_404(Course, slug=slug, instructor=request.user)
    template_name = 'instructor/_confirm_delete.html' if is_ajax(request) else 'instructor/confirm_delete.html'

    if request.method == 'POST':
        course.delete()
        messages.success(request, f'Course "{course.title}" deleted successfully.')
        if is_ajax(request):
            return JsonResponse({'success': True, 'message': f'Course "{course.title}" deleted successfully!', 'redirect_url': str(redirect('course_list').url)})
        return redirect('course_list')
    
    context = {'object': course, 'type': 'course', 'course_slug': course.slug}
    if is_ajax(request):
        return render(request, template_name, context)
    return render(request, template_name, context)


# --- Course Detail and Content Management Views ---

@login_required
def course_detail(request, slug):
    """
    Displays the details of a specific course.
    Allows instructors to manage modules/lessons/content.
    Allows students to view published courses.
    """
    course = get_object_or_404(Course, slug=slug)

    # Access control:
    # Instructors can view their own courses (published or not).
    # Students can view only published courses.
    if request.user.is_instructor and course.instructor != request.user:
        messages.error(request, "You do not have permission to view this course.")
        return redirect('dashboard')
    elif request.user.is_student and not course.is_published:
        messages.error(request, "This course is not yet published.")
        return redirect('dashboard')

    return render(request, 'course_detail.html', {'course': course})

@login_required
@user_passes_test(is_instructor)
def module_create(request, course_slug):
    """
    Allows an instructor to add a new module to their course.
    """
    course = get_object_or_404(Course, slug=course_slug, instructor=request.user)
    template_name = 'instructor/_module_form.html' if is_ajax(request) else 'instructor/module_form.html'

    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            messages.success(request, f'Module "{module.title}" added successfully to {course.title}.')
            if is_ajax(request):
                return JsonResponse({'success': True, 'message': f'Module "{module.title}" added successfully!'})
            return redirect('course_detail', slug=course.slug)
        else:
            if is_ajax(request):
                form_html = render_to_string(template_name, {'form': form, 'course': course, 'page_title': 'Add New Module'}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html, 'error': 'Validation failed.'})
            messages.error(request, 'Failed to add module. Please correct the errors.')
    else:
        form = ModuleForm()
    return render(request, template_name, {'form': form, 'course': course, 'page_title': 'Add New Module'})

@login_required
@user_passes_test(is_instructor)
def module_update(request, course_slug, module_id):
    """
    Allows an instructor to update a module in their course.
    """
    course = get_object_or_404(Course, slug=course_slug, instructor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    template_name = 'instructor/_module_form.html' if is_ajax(request) else 'instructor/module_form.html'

    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, f'Module "{module.title}" updated successfully.')
            if is_ajax(request):
                return JsonResponse({'success': True, 'message': f'Module "{module.title}" updated successfully!'})
            return redirect('course_detail', slug=course.slug)
        else:
            if is_ajax(request):
                form_html = render_to_string(template_name, {'form': form, 'course': course, 'page_title': f'Edit Module: {module.title}'}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html, 'error': 'Validation failed.'})
            messages.error(request, 'Failed to update module. Please correct the errors.')
    else:
        form = ModuleForm(instance=module)
    return render(request, template_name, {'form': form, 'course': course, 'page_title': f'Edit Module: {module.title}'})

@login_required
@user_passes_test(is_instructor)
def module_delete(request, course_slug, module_id):
    """
    Allows an instructor to delete a module.
    """
    course = get_object_or_404(Course, slug=course_slug, instructor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    template_name = 'instructor/_confirm_delete.html' if is_ajax(request) else 'instructor/confirm_delete.html'

    if request.method == 'POST':
        module.delete()
        messages.success(request, f'Module "{module.title}" deleted successfully.')
        if is_ajax(request):
            return JsonResponse({'success': True, 'message': f'Module "{module.title}" deleted successfully!'})
        return redirect('course_detail', slug=course.slug)
    
    context = {'object': module, 'type': 'module', 'course_slug': course_slug}
    if is_ajax(request):
        return render(request, template_name, context)
    return render(request, template_name, context)

@login_required
@user_passes_test(is_instructor)
def lesson_create(request, course_slug, module_id):
    """
    Allows an instructor to add a new lesson to a module.
    """
    course = get_object_or_404(Course, slug=course_slug, instructor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    template_name = 'instructor/_lesson_form.html' if is_ajax(request) else 'instructor/lesson_form.html'

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.save()
            messages.success(request, f'Lesson "{lesson.title}" added successfully to module "{module.title}".')
            if is_ajax(request):
                return JsonResponse({'success': True, 'message': f'Lesson "{lesson.title}" added successfully!'})
            return redirect('course_detail', slug=course.slug)
        else:
            if is_ajax(request):
                form_html = render_to_string(template_name, {'form': form, 'module': module, 'course': course, 'page_title': 'Add New Lesson'}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html, 'error': 'Validation failed.'})
            messages.error(request, 'Failed to add lesson. Please correct the errors.')
    else:
        form = LessonForm()
    return render(request, template_name, {'form': form, 'module': module, 'course': course, 'page_title': 'Add New Lesson'})

@login_required
@user_passes_test(is_instructor)
def lesson_update(request, course_slug, module_id, lesson_id):
    """
    Allows an instructor to update a lesson.
    """
    course = get_object_or_404(Course, slug=course_slug, instructor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    template_name = 'instructor/_lesson_form.html' if is_ajax(request) else 'instructor/lesson_form.html'

    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, f'Lesson "{lesson.title}" updated successfully.')
            if is_ajax(request):
                return JsonResponse({'success': True, 'message': f'Lesson "{lesson.title}" updated successfully!'})
            return redirect('course_detail', slug=course.slug)
        else:
            if is_ajax(request):
                form_html = render_to_string(template_name, {'form': form, 'module': module, 'course': course, 'page_title': f'Edit Lesson: {lesson.title}'}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html, 'error': 'Validation failed.'})
            messages.error(request, 'Failed to update lesson. Please correct the errors.')
    else:
        form = LessonForm(instance=lesson)
    return render(request, template_name, {'form': form, 'module': module, 'course': course, 'page_title': f'Edit Lesson: {lesson.title}'})

@login_required
@user_passes_test(is_instructor)
def lesson_delete(request, course_slug, module_id, lesson_id):
    """
    Allows an instructor to delete a lesson.
    """
    course = get_object_or_404(Course, slug=course_slug, instructor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    template_name = 'instructor/_confirm_delete.html' if is_ajax(request) else 'instructor/confirm_delete.html'

    if request.method == 'POST':
        lesson.delete()
        messages.success(request, f'Lesson "{lesson.title}" deleted successfully.')
        if is_ajax(request):
            return JsonResponse({'success': True, 'message': f'Lesson "{lesson.title}" deleted successfully!'})
        return redirect('course_detail', slug=course.slug)
    
    context = {'object': lesson, 'type': 'lesson', 'course_slug': course_slug, 'module_id': module_id}
    if is_ajax(request):
        return render(request, template_name, context)
    return render(request, template_name, context)

@login_required
@user_passes_test(is_instructor)
def content_create(request, course_slug, module_id, lesson_id):
    """
    Allows an instructor to add new content to a lesson.
    Handles file uploads.
    """
    course = get_object_or_404(Course, slug=course_slug, instructor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    template_name = 'instructor/_content_form.html' if is_ajax(request) else 'instructor/content_form.html'

    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES)
        if form.is_valid():
            content = form.save(commit=False)
            content.lesson = lesson
            content.save()
            messages.success(request, f'Content "{content.title}" added successfully to lesson "{lesson.title}".')
            if is_ajax(request):
                return JsonResponse({'success': True, 'message': f'Content "{content.title}" added successfully!'})
            return redirect('course_detail', slug=course.slug)
        else:
            if is_ajax(request):
                form_html = render_to_string(template_name, {'form': form, 'lesson': lesson, 'module': module, 'course': course, 'page_title': 'Add New Content'}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html, 'error': 'Validation failed.'})
            messages.error(request, 'Failed to add content. Please correct the errors.')
    else:
        form = ContentForm()
    return render(request, template_name, {'form': form, 'lesson': lesson, 'module': module, 'course': course, 'page_title': 'Add New Content'})

@login_required
@user_passes_test(is_instructor)
def content_update(request, course_slug, module_id, lesson_id, content_id):
   
    course = get_object_or_404(Course, slug=course_slug, instructor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    content = get_object_or_404(Content, id=content_id, lesson=lesson)
    template_name = 'instructor/_content_form.html' if is_ajax(request) else 'instructor/content_form.html'

    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            messages.success(request, f'Content "{content.title}" updated successfully.')
            if is_ajax(request):
                return JsonResponse({'success': True, 'message': f'Content "{content.title}" updated successfully!'})
            return redirect('course_detail', slug=course.slug)
        else:
            if is_ajax(request):
                form_html = render_to_string(template_name, {'form': form, 'lesson': lesson, 'module': module, 'course': course, 'page_title': f'Edit Content: {content.title}'}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html, 'error': 'Validation failed.'})
            messages.error(request, 'Failed to update content. Please correct the errors.')
    else:
        form = ContentForm(instance=content)
    return render(request, template_name, {'form': form, 'lesson': lesson, 'module': module, 'course': course, 'page_title': f'Edit Content: {content.title}'})

@login_required
@user_passes_test(is_instructor)
def content_delete(request, course_slug, module_id, lesson_id, content_id):
    """
    Allows an instructor to delete content.
    """
    course = get_object_or_404(Course, slug=course_slug, instructor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    content = get_object_or_404(Content, id=content_id, lesson=lesson)
    template_name = 'instructor/_confirm_delete.html' if is_ajax(request) else 'instructor/confirm_delete.html'

    if request.method == 'POST':
        content.delete()
        messages.success(request, f'Content "{content.title}" deleted successfully.')
        if is_ajax(request):
            return JsonResponse({'success': True, 'message': f'Content "{content.title}" deleted successfully!'})
        return redirect('course_detail', slug=course.slug)
    
    context = {'object': content, 'type': 'content', 'course_slug': course_slug, 'module_id': module_id, 'lesson_id': lesson_id}
    if is_ajax(request):
        return render(request, template_name, context)
    return render(request, template_name, context)


@login_required
def content_detail(request, course_slug, module_id, lesson_id, content_id):
    """
    Displays the content of a specific lesson.
    Students can view published content.
    Instructors can view their own content (published or not).
    """
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    content = get_object_or_404(Content, id=content_id, lesson=lesson)

    if request.user.is_instructor and course.instructor != request.user:
        messages.error(request, "You do not have permission to view this content.")
        return redirect('dashboard')
    elif request.user.is_student and not course.is_published:
        messages.error(request, "This course is not yet published.")
        return redirect('dashboard')

    context = {
        'course': course,
        'module': module,
        'lesson': lesson,
        'content': content,
    }
    return render(request, 'content_detail.html', context)
