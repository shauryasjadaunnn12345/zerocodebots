from django.db import models

# Create your models here.
# projects/models.py
from django.db import models
from django.contrib.auth.models import User
import secrets
import string

def generate_bot_key():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

class Project(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    bot_key = models.CharField(max_length=64, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Agent configuration
    allowed_intents = models.JSONField(
        default=list,  # interpreted as "all intents allowed" by default
        blank=True,
        help_text=(
            "List of enabled intents for this project. "
            "If empty or not set, all intents are treated as allowed."
        ),
    )
    workflow_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional workflow configuration for advanced agent behavior.",
    )
    voice_enabled = models.BooleanField(
        default=False,
        help_text="Enable optional voice (speech input and spoken responses) for this project.",
    )

    def save(self, *args, **kwargs):
    if not self.bot_key:
        self.bot_key = generate_bot_key()
    super().save(*args, **kwargs)




class QuestionAnswer(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='qas')
    question = models.CharField(max_length=255)
    answer = models.TextField(blank=True)
    image = models.ImageField(upload_to='answers/', blank=True, null=True)
    image_description = models.CharField(max_length=255, blank=True, null=True)  # ✅ optional

from django.contrib.auth.models import User
import random

class OTPVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.save()


class Lead(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='leads')
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name or 'Unnamed lead'} - {self.email or 'no-email'}"


class AnalyticsEvent(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='analytics_events')
    event_type = models.CharField(max_length=64)
    metadata = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project_id} - {self.event_type} @ {self.timestamp}"


class Feedback(models.Model):
    """
    Stores explicit user feedback about a bot response.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='feedbacks')
    question = models.TextField(blank=True)
    response = models.TextField(blank=True)
    rating = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True)
    selected_option = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    bot_response = models.ForeignKey('BotResponse', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')

    def __str__(self):
        return f"Feedback {self.id} for project {self.project_id}"


class ConversationContext(models.Model):
    """
    Minimal context memory storage per project / session.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='contexts')
    session_key = models.CharField(max_length=255, blank=True, null=True)
    key = models.CharField(max_length=255)
    value = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['project', 'session_key', 'key'])]


class BotResponse(models.Model):
    """
    Stores bot responses with optional confidence and structured payload
    (e.g., MCQ options or clarification prompts) for analytics and tuning.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='responses')
    question = models.TextField(blank=True)
    response = models.TextField(blank=True)
    confidence = models.FloatField(blank=True, null=True)
    payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response {self.id} (proj {self.project_id})"


class Blog(models.Model):
    """
    Blog model for creating and managing blog posts
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    excerpt = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    category = models.CharField(max_length=100, default='General', choices=[
        ('AI', 'AI'),
        ('Chatbots', 'Chatbots'),
        ('Business', 'Business'),
        ('Technology', 'Technology'),
        ('General', 'General'),
        ('Tutorial', 'Tutorial'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    views = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_slug(self):
        from django.utils.text import slugify
        if not self.slug:
            self.slug = slugify(self.title)
        return self.slug


class Newsletter(models.Model):
    """
    Newsletter subscription model to store subscriber emails and track subscription status.
    """
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):

        return f"{self.email} - {'Active' if self.is_active else 'Inactive'}"

