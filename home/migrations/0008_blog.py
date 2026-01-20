# Generated migration for Blog model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('home', '0007_feedback_bot_response'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True)),
                ('excerpt', models.CharField(blank=True, max_length=255)),
                ('content', models.TextField()),
                ('featured_image', models.ImageField(blank=True, null=True, upload_to='blog_images/')),
                ('category', models.CharField(choices=[('AI', 'AI'), ('Chatbots', 'Chatbots'), ('Business', 'Business'), ('Technology', 'Technology'), ('General', 'General'), ('Tutorial', 'Tutorial')], default='General', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_published', models.BooleanField(default=True)),
                ('views', models.IntegerField(default=0)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blogs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
