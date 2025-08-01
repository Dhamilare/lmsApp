# Generated by Django 5.2.4 on 2025-07-21 20:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lmsApp', '0003_studentcontentprogress'),
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('order', models.PositiveIntegerField(default=0, help_text='Order of the question within the quiz.')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
                ('is_correct', models.BooleanField(default=False)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='lmsApp.question')),
            ],
            options={
                'unique_together': {('question', 'text')},
            },
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('duration_minutes', models.PositiveIntegerField(default=0, help_text='Duration of the quiz in minutes (0 for no time limit).')),
                ('pass_percentage', models.PositiveIntegerField(default=70, help_text='Minimum percentage required to pass the quiz.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lesson', models.OneToOneField(blank=True, help_text="Optional: Link this quiz to a specific lesson. If linked, a 'quiz' content type should point to this quiz.", null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quiz', to='lmsApp.lesson')),
            ],
            options={
                'verbose_name_plural': 'Quizzes',
            },
        ),
        migrations.AddField(
            model_name='question',
            name='quiz',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='lmsApp.quiz'),
        ),
        migrations.CreateModel(
            name='StudentQuizAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(blank=True, decimal_places=2, help_text='Score as a percentage (e.g., 85.50).', max_digits=5, null=True)),
                ('passed', models.BooleanField(default=False)),
                ('attempt_date', models.DateTimeField(auto_now_add=True)),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='lmsApp.quiz')),
                ('student', models.ForeignKey(limit_choices_to={'is_student': True}, on_delete=django.db.models.deletion.CASCADE, related_name='quiz_attempts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-attempt_date'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='question',
            unique_together={('quiz', 'order')},
        ),
        migrations.CreateModel(
            name='StudentAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chosen_option', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chosen_by_students', to='lmsApp.option')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_answers', to='lmsApp.question')),
                ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='lmsApp.studentquizattempt')),
            ],
            options={
                'unique_together': {('attempt', 'question')},
            },
        ),
    ]
