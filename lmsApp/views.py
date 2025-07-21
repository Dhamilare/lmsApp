# instructor/views.py (Updated for AJAX Modals)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q, Max
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
    Includes course search functionality for students.
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
        context['enrolled_courses'] = Enrollment.objects.filter(student=user).select_related('course').order_by('-enrolled_at')
        
        # Calculate progress for each enrolled course
        for enrollment in context['enrolled_courses']:
            total_contents = Content.objects.filter(lesson__module__course=enrollment.course).count()
            completed_contents = StudentContentProgress.objects.filter(
                student=user,
                content__lesson__module__course=enrollment.course,
                completed=True
            ).count()
            
            enrollment.progress_percentage = 0
            if total_contents > 0:
                enrollment.progress_percentage = int((completed_contents / total_contents) * 100)
            
            # Update enrollment.completed based on 100% progress
            if enrollment.progress_percentage == 100 and not enrollment.completed:
                enrollment.completed = True
                enrollment.save(update_fields=['completed'])
            elif enrollment.progress_percentage < 100 and enrollment.completed:
                # If progress drops below 100% (e.g., instructor adds new content), mark as incomplete
                enrollment.completed = False
                enrollment.save(update_fields=['completed'])

        # Course Search Logic for Students
        search_query = request.GET.get('q')
        if search_query:
            # Filter available courses by title or description
            context['available_courses'] = Course.objects.filter(
                is_published=True
            ).exclude(
                enrollments__student=user
            ).filter(
                Q(title__icontains=search_query) | Q(description__icontains=search_query)
            ).order_by('-created_at')
            context['search_query'] = search_query # Pass query back to template for input field
        else:
            context['available_courses'] = Course.objects.filter(is_published=True).exclude(enrollments__student=user).order_by('-created_at')[:5] # Show some available courses not yet enrolled
    
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
            return redirect('instructor_list')
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
    Allows students to view published courses and enroll.
    """
    course = get_object_or_404(Course, slug=slug)
    is_enrolled = False
    student_progress = None # Initialize student_progress
    if request.user.is_authenticated and request.user.is_student:
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()

        student_progress_map = {
            p.content_id: p.completed
            for p in StudentContentProgress.objects.filter(
                student=request.user,
                content__lesson__module__course=course
            )
        }
        for module in course.modules.all():
            for lesson in module.lessons.all():
                for content_item in lesson.contents.all():
                    content_item.is_completed = student_progress_map.get(content_item.id, False)

    can_access_content = False
    if request.user.is_authenticated:
        if request.user.is_instructor and course.instructor == request.user:
            can_access_content = True
        elif request.user.is_student and course.is_published and is_enrolled:
            can_access_content = True

    if request.user.is_instructor and course.instructor != request.user:
        messages.error(request, "You do not have permission to view this course.")
        return redirect('dashboard')
    elif request.user.is_student and not course.is_published and not is_enrolled:
        messages.error(request, "This course is not yet published or you are not enrolled.")
        return redirect('dashboard')

    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'can_access_content': can_access_content, 
    }
    return render(request, 'course_detail.html', context)

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
    Automatically sets the 'order' field.
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
            
            # --- FIX: Automatically set the order for new content ---
            # Get the maximum existing order for content within this lesson
            max_order = Content.objects.filter(lesson=lesson).aggregate(Max('order'))['order__max']
            # Set the new content's order to max_order + 1, or 1 if no content exists yet
            content.order = (max_order or 0) + 1
            # --- END FIX ---

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

    student_progress = None
    if request.user.is_authenticated and request.user.is_student:
        # Get or create the progress record for this specific content item
        student_progress, _ = StudentContentProgress.objects.get_or_create(
            student=request.user,
            content=content
        )

    # Determine if the user can access content (instructor of this course OR enrolled student)
    can_view_content_page = False
    quiz_obj = None # Initialize quiz_obj
    if request.user.is_authenticated:
        if request.user.is_instructor and course.instructor == request.user:
            can_view_content_page = True
        elif request.user.is_student and course.is_published and Enrollment.objects.filter(student=request.user, course=course).exists():
            can_view_content_page = True

    if not can_view_content_page:
        messages.error(request, "You do not have permission to view this content.")
        return redirect('dashboard')

    # If content is a quiz, fetch the associated quiz object
    if content.content_type == 'quiz':
        quiz_obj = Quiz.objects.filter(lesson=lesson).first()
        if not quiz_obj:
            messages.warning(request, "This quiz content is not linked to an actual quiz yet.")


    context = {
        'course': course,
        'module': module,
        'lesson': lesson,
        'content': content,
        'student_progress': student_progress,
        'quiz_obj': quiz_obj,
    }
    return render(request, 'content_detail.html', context)

@login_required
@user_passes_test(is_student)
def enroll_course(request, slug):
    """
    Allows a student to enroll in a course.
    """
    course = get_object_or_404(Course, slug=slug)

    if not course.is_published:
        if is_ajax(request):
            return JsonResponse({'success': False, 'error': 'Cannot enroll in an unpublished course.'}, status=400)
        messages.error(request, 'Cannot enroll in an unpublished course.')
        return redirect('course_detail', slug=course.slug)

    if Enrollment.objects.filter(student=request.user, course=course).exists():
        if is_ajax(request):
            return JsonResponse({'success': False, 'error': 'You are already enrolled in this course.'}, status=400)
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('course_detail', slug=course.slug)

    try:
        with transaction.atomic():
            Enrollment.objects.create(student=request.user, course=course)
            messages.success(request, f'Successfully enrolled in "{course.title}"!')
            if is_ajax(request):
                return JsonResponse({'success': True, 'message': f'Successfully enrolled in "{course.title}"!', 'redirect_url': str(redirect('course_detail', slug=course.slug).url)})
            return redirect('course_detail', slug=course.slug)
    except Exception as e:
        messages.error(request, f'Failed to enroll in course: {e}')
        if is_ajax(request):
            return JsonResponse({'success': False, 'error': f'Failed to enroll in course: {e}'}, status=500)
        return redirect('course_detail', slug=course.slug)
    

@login_required
@user_passes_test(is_student) # Only students can mark content as complete
def mark_content_completed(request, course_slug, module_id, lesson_id, content_id):
    """
    Allows a student to mark a content item as completed (or incomplete).
    This is an AJAX endpoint.
    """
    if not is_ajax(request) or request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    content = get_object_or_404(Content, id=content_id, lesson=lesson)
    student = request.user

    # Ensure student is enrolled in the course to mark content complete
    if not Enrollment.objects.filter(student=student, course=course).exists():
        return JsonResponse({'success': False, 'error': 'You must be enrolled in this course to mark content.'}, status=403)

    try:
        progress, created = StudentContentProgress.objects.get_or_create(
            student=student,
            content=content,
            defaults={'completed': True, 'completed_at': timezone.now()}
        )
        if not created:
            # Toggle completed status
            progress.completed = not progress.completed
            if progress.completed:
                progress.completed_at = timezone.now()
            else:
                progress.completed_at = None
            progress.save()
        
        status_message = "marked as complete." if progress.completed else "marked as incomplete."
        messages.success(request, f'Content "{content.title}" {status_message}')
        return JsonResponse({'success': True, 'completed': progress.completed, 'message': f'Content "{content.title}" {status_message}'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Failed to update progress: {e}'}, status=500)


@login_required
@user_passes_test(is_student)
def quiz_take(request, course_slug, module_id, lesson_id, content_id):
    """
    Allows a student to take a quiz.
    """
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    content = get_object_or_404(Content, id=content_id, lesson=lesson, content_type='quiz')
    quiz = get_object_or_404(Quiz, lesson=lesson) # Assuming one quiz per lesson for now

    # Access control: Student must be enrolled and course published
    if not Enrollment.objects.filter(student=request.user, course=course).exists() or not course.is_published:
        messages.error(request, "You are not authorized to take this quiz.")
        return redirect('course_detail', slug=course.slug)

    # Check if quiz has questions
    if not quiz.questions.exists():
        messages.info(request, "This quiz has no questions yet.")
        return redirect('content_detail', course_slug=course.slug, module_id=module.id, lesson_id=lesson.id, content_id=content.id)

    form = QuizForm(quiz=quiz) # Initialize form with the quiz instance

    context = {
        'course': course,
        'module': module,
        'lesson': lesson,
        'content': content,
        'quiz': quiz,
        'form': form,
    }
    return render(request, 'student/quiz_take.html', context)

@login_required
@user_passes_test(is_student)
def quiz_submit(request, course_slug, module_id, lesson_id, content_id):
    """
    Handles the submission and grading of a quiz.
    """
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    content = get_object_or_404(Content, id=content_id, lesson=lesson, content_type='quiz')
    quiz = get_object_or_404(Quiz, lesson=lesson)

    # Access control: Student must be enrolled and course published
    if not Enrollment.objects.filter(student=request.user, course=course).exists() or not course.is_published:
        messages.error(request, "You are not authorized to submit this quiz.")
        return redirect('course_detail', slug=course.slug)

    if request.method == 'POST':
        form = QuizForm(request.POST, quiz=quiz)
        if form.is_valid():
            total_questions = quiz.questions.count()
            correct_answers_count = 0
            student_answers_to_save = []

            with transaction.atomic():
                # Create a new quiz attempt record
                attempt = StudentQuizAttempt.objects.create(
                    student=request.user,
                    quiz=quiz,
                    score=0, # Will update later
                    passed=False
                )

                for question in quiz.questions.all():
                    field_name = f'question_{question.id}'
                    chosen_option_id = form.cleaned_data.get(field_name)

                    chosen_option = None
                    if chosen_option_id:
                        chosen_option = get_object_or_404(Option, id=chosen_option_id, question=question)

                    # Save student's answer
                    student_answers_to_save.append(
                        StudentAnswer(
                            attempt=attempt,
                            question=question,
                            chosen_option=chosen_option
                        )
                    )

                    # Check if the chosen option is correct
                    if chosen_option and chosen_option.is_correct:
                        correct_answers_count += 1
                
                # Bulk create student answers
                StudentAnswer.objects.bulk_create(student_answers_to_save)

                # Calculate score
                score_percentage = 0
                if total_questions > 0:
                    score_percentage = (correct_answers_count / total_questions) * 100
                
                # Update the attempt with score and pass/fail status
                attempt.score = round(score_percentage, 2)
                attempt.passed = (score_percentage >= quiz.pass_percentage)
                attempt.save()

                messages.success(request, f'Quiz "{quiz.title}" submitted! Your score: {attempt.score:.2f}%')
                return redirect('quiz_result', course_slug=course.slug, module_id=module.id, lesson_id=lesson.id, content_id=content.id, attempt_id=attempt.id)
        else:
            # If form is not valid, re-render the quiz_take page with errors
            messages.error(request, "Please correct the errors below.")
            context = {
                'course': course,
                'module': module,
                'lesson': lesson,
                'content': content,
                'quiz': quiz,
                'form': form,
            }
            return render(request, 'student/quiz_take.html', context)
    else:
        messages.error(request, "Invalid request method for quiz submission.")
        return redirect('quiz_take', course_slug=course.slug, module_id=module.id, lesson_id=lesson.id, content_id=content.id)

@login_required
@user_passes_test(is_student)
def quiz_result(request, course_slug, module_id, lesson_id, content_id, attempt_id):
    """
    Displays the result of a student's quiz attempt.
    """
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    content = get_object_or_404(Content, id=content_id, lesson=lesson, content_type='quiz')
    quiz = get_object_or_404(Quiz, lesson=lesson)
    attempt = get_object_or_404(StudentQuizAttempt, id=attempt_id, student=request.user, quiz=quiz)

    # Access control: Student must be enrolled and course published
    if not Enrollment.objects.filter(student=request.user, course=course).exists() or not course.is_published:
        messages.error(request, "You are not authorized to view this quiz result.")
        return redirect('course_detail', slug=course.slug)

    # Fetch all questions and their options for the quiz
    questions_with_answers = []
    for question in quiz.questions.all().order_by('order'):
        options = list(question.options.all())
        student_answer = StudentAnswer.objects.filter(attempt=attempt, question=question).first()
        
        chosen_option_id = student_answer.chosen_option.id if student_answer and student_answer.chosen_option else None
        
        questions_with_answers.append({
            'question': question,
            'options': options,
            'chosen_option_id': chosen_option_id,
            'is_correct': student_answer.chosen_option.is_correct if student_answer and student_answer.chosen_option else False,
            'correct_option': next((opt for opt in options if opt.is_correct), None)
        })

    context = {
        'course': course,
        'module': module,
        'lesson': lesson,
        'content': content,
        'quiz': quiz,
        'attempt': attempt,
        'questions_with_answers': questions_with_answers,
    }
    return render(request, 'student/quiz_result.html', context)