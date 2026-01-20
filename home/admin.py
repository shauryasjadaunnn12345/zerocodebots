from django.contrib import admin
from home.models import Project, QuestionAnswer, Lead, AnalyticsEvent, Feedback, ConversationContext, BotResponse, Blog, Newsletter


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'user', 'created_at')


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
	list_display = ('title', 'author', 'category', 'is_published', 'created_at', 'views')
	list_filter = ('category', 'is_published', 'created_at')
	search_fields = ('title', 'content', 'author__username')
	prepopulated_fields = {'slug': ('title',)}


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
	list_display = ('email', 'is_active', 'subscribed_at', 'ip_address')
	list_filter = ('is_active', 'subscribed_at')
	search_fields = ('email',)
	readonly_fields = ('subscribed_at', 'ip_address', 'user_agent')

admin.site.register(QuestionAnswer)
admin.site.register(Lead)
admin.site.register(AnalyticsEvent)
admin.site.register(Feedback)
admin.site.register(ConversationContext)
admin.site.register(BotResponse)
