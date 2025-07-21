from django.contrib.auth import get_user_model
from lmsApp.models import Course, Module, Lesson, Content

User = get_user_model()

# 1. Get or create the instructor user
instructor_user, _ = User.objects.get_or_create(
    username="devops_instructor",
    defaults={
        "email": "devops_instructor@example.com",
        "password": "securepass456"  # Use user.set_password() if running interactively
    }
)

# 2. Create the DevOps Course
course = Course.objects.create(
    title="Introduction to DevOps",
    description="Learn the principles, practices, and tools that bridge development and operations.",
    instructor=instructor_user
)

# 3. Create Modules
module1 = Module.objects.create(course=course, title="DevOps Fundamentals", description="What is DevOps and why it matters", order=1)
module2 = Module.objects.create(course=course, title="CI/CD & Automation", description="Key DevOps practices", order=2)

# 4. Create Lessons
lesson1 = Lesson.objects.create(module=module1, title="What is DevOps?", description="Origins and philosophy", order=1)
lesson2 = Lesson.objects.create(module=module1, title="DevOps Lifecycle", description="Stages of DevOps workflow", order=2)

lesson3 = Lesson.objects.create(module=module2, title="Introduction to CI/CD", description="Concepts and benefits", order=1)
lesson4 = Lesson.objects.create(module=module2, title="Automation Tools", description="Jenkins, GitHub Actions, etc.", order=2)

# 5. Add Content

# Lesson 1
Content.objects.create(
    lesson=lesson1,
    title="DevOps Explained - Video",
    content_type="video",
    video_url="https://www.youtube.com/watch?v=1KqfN6tM2n0",
    order=1
)
Content.objects.create(
    lesson=lesson1,
    title="DevOps Overview PDF",
    content_type="pdf",
    file="lms_content/devops_intro.pdf",
    order=2
)

# Lesson 2
Content.objects.create(
    lesson=lesson2,
    title="DevOps Lifecycle Diagram",
    content_type="slide",
    file="lms_content/devops_lifecycle_slide.pdf",
    order=1
)
Content.objects.create(
    lesson=lesson2,
    title="Quiz: DevOps Lifecycle",
    content_type="quiz",
    order=2
)

# Lesson 3
Content.objects.create(
    lesson=lesson3,
    title="CI/CD Basics",
    content_type="text",
    text_content="Continuous Integration (CI) and Continuous Deployment (CD) are key practices in DevOps...",
    order=1
)
Content.objects.create(
    lesson=lesson3,
    title="CI/CD Workflow Video",
    content_type="video",
    video_url="https://www.youtube.com/watch?v=scEDHsr3APg",
    order=2
)

# Lesson 4
Content.objects.create(
    lesson=lesson4,
    title="Automation Tools Slide",
    content_type="slide",
    file="lms_content/devops_tools.pdf",
    order=1
)
Content.objects.create(
    lesson=lesson4,
    title="Assignment: Build a CI/CD Pipeline",
    content_type="assignment",
    text_content="Set up a CI/CD pipeline for a sample Python app using GitHub Actions or Jenkins.",
    order=2
)

print("✅ DevOps course data seeded successfully.")
