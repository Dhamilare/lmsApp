# core/forms.py (Instructor is_staff=False Corrected)
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Div, HTML
from .models import *
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.forms import inlineformset_factory

class StudentRegistrationForm(forms.ModelForm):
    """
    Custom form for student registration, providing explicit control over fields.
    Only allows students to register directly.
    """
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
        help_text="" # Set help_text to an empty string to remove it
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}),
        help_text="" # Set help_text to an empty string to remove it
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Choose a username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email address'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Your first name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Your last name'}),
        }
        # Override help_texts coming from the model fields
        help_texts = {
            'username': '', # Remove help_text for username
            'email': '',    # Remove help_text for email (if any default exists)
            'first_name': '', # Remove help_text for first_name (if any default exists)
            'last_name': '',  # Remove help_text for last_name (if any default exists)
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('username', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('email', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('first_name', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('last_name', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('password', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('password2', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Submit('submit', 'Register', css_class='w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 mt-4')
        )

    def clean_password2(self):
        """
        Validates that password and password2 match.
        Also applies Django's password validation rules.
        """
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if password and password2 and password != password2:
            raise ValidationError("Passwords don't match.")

        # Apply Django's default password validators
        try:
            validate_password(password, self.instance)
        except ValidationError as e:
            self.add_error('password', e) # Add error to the 'password' field
            raise

        return password2

    def save(self, commit=True):
        """
        Saves the user instance and sets the password correctly.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"]) # Set hashed password
        user.is_student = True # Ensure new users are students
        user.is_instructor = False # Ensure new users are not instructors
        user.is_staff = False # Ensure new users are not staff/admin
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    """
    Custom form for user login.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('username', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('password', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Submit('submit', 'Login', css_class='w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 mt-4')
        )

class InstructorCreationForm(UserCreationForm):
    """
    Form for Admin to create Instructor accounts.
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('username', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('email', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('first_name', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('last_name', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('password', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('password2', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Submit('submit', 'Create Instructor', css_class='w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 mt-4')
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_instructor = True # Set new user as instructor
        user.is_student = False # Ensure they are not students
        user.is_staff = False # Corrected: Instructors are NOT staff/admin
        if commit:
            user.save()
        return user
    
class InstructorUpdateForm(UserChangeForm):
    """
    Form for Admin to update Instructor accounts.
    Excludes password fields for security, as password changes should be separate.
    """
    password = None # Exclude password field from this form

    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_instructor', 'is_student')
        # Remove help_texts for all fields if desired, similar to StudentRegistrationForm
        help_texts = {f: '' for f in fields} # Set all help_texts to empty string

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('username', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('email', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('first_name', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('last_name', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('is_active', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('is_staff', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('is_instructor', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('is_student', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Submit('submit', 'Update Instructor', css_class='w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 mt-4')
        )
        # Remove help_text for specific fields if they override the general help_texts setting
        self.fields['is_staff'].help_text = ''
        self.fields['is_active'].help_text = ''
        self.fields['is_instructor'].help_text = ''
        self.fields['is_student'].help_text = ''

class CourseForm(forms.ModelForm):
    """
    Form for creating and updating Course objects.
    """
    class Meta:
        model = Course
        fields = ['title', 'description', 'price', 'is_published', 'thumbnail']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('title', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('description', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('price', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('is_published', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('thumbnail', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Submit('submit', 'Save Course', css_class='w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 mt-4')
        )

class ModuleForm(forms.ModelForm):
    """
    Form for creating and updating Module objects.
    """
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('title', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('description', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('order', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Submit('submit', 'Save Module', css_class='w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 mt-4')
        )

class LessonForm(forms.ModelForm):
    """
    Form for creating and updating Lesson objects.
    """
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('title', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('description', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('order', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Submit('submit', 'Save Lesson', css_class='w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 mt-4')
        )

class ContentForm(forms.ModelForm):
    """
    Form for creating and updating Content objects.
    Handles conditional display of fields based on content_type.
    """
    class Meta:
        model = Content
        fields = ['title', 'content_type', 'file', 'text_content', 'video_url', 'order']
        widgets = {
            'text_content': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('title', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('content_type', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            # These fields will be conditionally shown/hidden via JavaScript in the template
            Field('file', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('text_content', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('video_url', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Field('order', css_class='rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'),
            Submit('submit', 'Save Content', css_class='w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 mt-4')
        )

    def clean(self):
        """
        Custom cleaning to ensure only relevant content fields are populated
        based on the selected content_type.
        """
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        file = cleaned_data.get('file')
        text_content = cleaned_data.get('text_content')
        video_url = cleaned_data.get('video_url')

        if content_type == 'video':
            if not video_url and not file:
                raise ValidationError("For video content, either a video URL or a file upload is required.")
            # Clear other fields
            cleaned_data['text_content'] = None
        elif content_type == 'pdf' or content_type == 'slide':
            if not file:
                raise ValidationError(f"For {content_type} content, a file upload is required.")
            # Clear other fields
            cleaned_data['text_content'] = None
            cleaned_data['video_url'] = None
        elif content_type == 'text':
            if not text_content:
                raise ValidationError("For text content, the text field cannot be empty.")
            # Clear other fields
            cleaned_data['file'] = None
            cleaned_data['video_url'] = None
        elif content_type == 'quiz' or content_type == 'assignment':
            cleaned_data['file'] = None
            cleaned_data['text_content'] = None
            cleaned_data['video_url'] = None
        
        return cleaned_data
    

# --- Quiz Forms ---

class OptionForm(forms.ModelForm):
    """
    Form for individual answer options within a question.
    """
    class Meta:
        model = Option
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-checkbox h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500'}),
        }

# Inline formset for Options within a Question
OptionFormSet = inlineformset_factory(
    Question,
    Option,
    form=OptionForm,
    extra=4,  # Number of empty forms to display
    min_num=2, # Minimum number of options required
    max_num=4, # Maximum number of options allowed
    validate_min=True,
    can_delete=False, # Options should not be deleted independently in quiz creation
    labels={
        'text': 'Option Text',
        'is_correct': 'Is Correct?'
    }
)

class QuestionForm(forms.ModelForm):
    """
    Form for individual quiz questions.
    """
    class Meta:
        model = Question
        fields = ['text', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-textarea mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}),
        }

# Inline formset for Questions within a Quiz
QuestionFormSet = inlineformset_factory(
    Quiz,
    Question,
    form=QuestionForm,
    extra=1, # Number of empty forms to display
    min_num=1, # Minimum number of questions required
    validate_min=True,
    can_delete=True,
    labels={
        'text': 'Question Text',
        'order': 'Order'
    }
)

class QuizForm(forms.Form):
    """
    A dynamic form for taking a quiz.
    It generates fields based on the questions associated with a given Quiz instance.
    """
    def __init__(self, *args, **kwargs):
        self.quiz = kwargs.pop('quiz', None)
        super().__init__(*args, **kwargs)

        if not self.quiz:
            raise ValueError("Quiz instance must be provided to QuizForm.")

        for question in self.quiz.questions.all().order_by('order'):
            # Create a list of (value, label) tuples for choices
            choices = [(option.id, option.text) for option in question.options.all()]
            
            # Add a RadioSelect field for each question
            self.fields[f'question_{question.id}'] = forms.ChoiceField(
                label=f"{question.order}. {question.text}",
                choices=choices,
                widget=forms.RadioSelect(attrs={'class': 'form-radio h-4 w-4 text-indigo-600'}),
                required=True, # All questions are required to be answered
            )
            self.fields[f'question_{question.id}'].widget.attrs['data-question-id'] = question.id
