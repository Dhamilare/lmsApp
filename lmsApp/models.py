# core/models.py (Updated with Slug)
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds fields to differentiate between instructors and students.
    is_staff field from AbstractUser will be used for Admin.
    """
    is_instructor = models.BooleanField(default=False)
    is_student = models.BooleanField(default=True) # Default to True for new registrations

    def __str__(self):
        return self.username

class Course(models.Model):
    """
    Represents a course in the LMS.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught', limit_choices_to={'is_instructor': True})
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # For paid courses
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    thumbnail = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL for the course thumbnail image. Example: https://placehold.co/600x400/E0E7FF/4338CA?text=Course+Thumbnail"
    )
    slug = models.SlugField(unique=True, max_length=255, blank=True) # New slug field

    def save(self, *args, **kwargs):
        """
        Overrides the save method to automatically generate a unique slug
        from the course title if one is not provided.
        """
        if not self.slug:
            base_slug = slugify(self.title)
            unique_slug = base_slug
            num = 1
            # Check for uniqueness and append a number if necessary
            while Course.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class Module(models.Model):
    """
    Represents a module or chapter within a course.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of the module within the course.")

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    class Meta:
        ordering = ['order']
        unique_together = ('course', 'order')

class Lesson(models.Model):
    """
    Represents an individual lesson within a module.
    """
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of the lesson within the module.")
    # Duration could be added here if needed, e.g., models.DurationField()

    def __str__(self):
        return f"{self.module.course.title} - {self.module.title} - {self.title}"

    class Meta:
        ordering = ['order']
        unique_together = ('module', 'order')

class Content(models.Model):
    """
    Represents various types of content within a lesson (video, PDF, text, etc.).
    """
    CONTENT_TYPES = (
        ('video', 'Video'),
        ('pdf', 'PDF Document'),
        ('text', 'Text/Notes'),
        ('slide', 'Presentation Slides'),
        ('quiz', 'Quiz'), # Placeholder for quiz content
        ('assignment', 'Assignment'), # Placeholder for assignment content
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    file = models.FileField(upload_to='lms_content/', blank=True, null=True, help_text="Upload video, PDF, or other files.")
    text_content = models.TextField(blank=True, null=True, help_text="For text-based content (e.g., notes).")
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL for external video (e.g., YouTube, Vimeo).")
    order = models.PositiveIntegerField(default=0, help_text="Order of the content within the lesson.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lesson.title} - {self.title} ({self.get_content_type_display()})"

    class Meta:
        ordering = ['order']
        unique_together = ('lesson', 'order')
