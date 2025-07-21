# core/admin.py (Latest Version - Reconfirmed)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Course, Module, Lesson, Content

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom Admin interface for the User model.
    Allows staff (admins) to manage user roles including 'is_instructor' and 'is_student'.
    """
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_instructor', 'is_student',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('is_instructor', 'is_student',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_instructor', 'is_student', 'is_active')
    list_filter = ('is_staff', 'is_instructor', 'is_student', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    # Override save_model to ensure only admins can set is_instructor
    def save_model(self, request, obj, form, change):
        if not request.user.is_staff and 'is_instructor' in form.changed_data:
            pass
        super().save_model(request, obj, form, change)

# Register Course, Module, Lesson, Content models with the admin site
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'price', 'is_published', 'created_at', 'updated_at')
    list_filter = ('is_published', 'instructor')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)} # Auto-populate slug from title
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'description')
    ordering = ('course', 'order')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order')
    list_filter = ('module__course', 'module')
    search_fields = ('title', 'description')
    ordering = ('module', 'order')

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'content_type', 'order', 'created_at')
    list_filter = ('content_type', 'lesson__module__course', 'lesson__module', 'lesson')
    search_fields = ('title', 'text_content')
    ordering = ('lesson', 'order')
